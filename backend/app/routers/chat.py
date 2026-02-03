"""POST /chat (Step 8-3) - 자연어 → LLM 추출 → 저장 → 한 줄 응답"""
from datetime import date
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ChatRequest
from app.services.audit import log_audit
from app.services.idempotency import get_cached_tx_id, save_idempotency
from app.services.normalizer import normalize_amount, normalize_category, normalize_date
from app.services.orchestrator import extract_transaction
from app.services.undo import save_undo_token

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    body: ChatRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    POST /chat
    자연어 입력 → LLM 추출 → 정규화 → 저장 → 한 줄 확인 응답.
    애매하면 질문 1개만 반환 (저장 안 함).
    """
    # LLM 추출
    result = await extract_transaction(body.user_id, body.message)

    if result["action"] == "clarify":
        return {
            "reply": result["reply"],
            "tx_id": None,
            "undo_token": None,
            "needs_clarification": True,
        }

    # action == "create"
    args = result["args"]
    user_id = args.get("user_id") or body.user_id
    idem_key = body.idem_key

    # idempotency: 캐시 확인
    if idem_key:
        cached = await get_cached_tx_id(session, user_id, idem_key)
        if cached:
            return {
                "reply": "이미 기록된 내역이에요.",
                "tx_id": str(cached),
                "undo_token": None,
                "needs_clarification": False,
            }

    # 정규화 (서버 최종 책임)
    raw_date = args.get("occurred_date") or ""
    if not raw_date:
        occurred_date = date.today()
    else:
        try:
            occurred_date = normalize_date(raw_date)
        except (ValueError, TypeError):
            occurred_date = date.today()
    try:
        amount = normalize_amount(args.get("amount", 0))
        category = normalize_category(args.get("category", "기타"))
    except (ValueError, TypeError) as e:
        return {
            "reply": f"입력 형식을 확인해주세요. ({e})",
            "tx_id": None,
            "undo_token": None,
            "needs_clarification": True,
        }

    if amount <= 0:
        return {
            "reply": "금액은 0보다 커야 해요.",
            "tx_id": None,
            "undo_token": None,
            "needs_clarification": True,
        }

    tx_type = args.get("type", "expense")
    if tx_type not in ("expense", "income"):
        tx_type = "expense"
    merchant = args.get("merchant")
    memo = args.get("memo")
    source_text = args.get("source_text") or body.message

    # 트랜잭션 생성
    insert_result = await session.execute(
        text("""
            INSERT INTO transactions (user_id, occurred_date, type, amount, currency, category, merchant, memo, source_text)
            VALUES (:user_id, :occurred_date, :type, :amount, :currency, :category, :merchant, :memo, :source_text)
            RETURNING tx_id
        """),
        {
            "user_id": user_id,
            "occurred_date": str(occurred_date),
            "type": tx_type,
            "amount": amount,
            "currency": "KRW",
            "category": category,
            "merchant": merchant,
            "memo": memo,
            "source_text": source_text,
        },
    )
    row = insert_result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="트랜잭션 생성 실패")
    tx_id = UUID(str(row[0]))

    # idempotency: 저장
    if idem_key:
        await save_idempotency(session, user_id, idem_key, tx_id)

    # 감사로그: create
    after_snapshot = {
        "tx_id": str(tx_id),
        "user_id": user_id,
        "occurred_date": str(occurred_date),
        "type": tx_type,
        "amount": amount,
        "currency": "KRW",
        "category": category,
        "merchant": merchant,
        "memo": memo,
        "source_text": source_text,
    }
    await log_audit(session, user_id, "create", tx_id=tx_id, after_snapshot=after_snapshot)

    # undo_token: Redis에 TTL 저장
    undo_token = str(uuid4())
    await save_undo_token(undo_token, tx_id)

    # 한 줄 확인 응답
    type_label = "지출" if tx_type == "expense" else "수입"
    reply = f"{occurred_date} {category} {type_label} {amount:,}원 기록했어요."

    return {
        "reply": reply,
        "tx_id": str(tx_id),
        "undo_token": undo_token,
        "needs_clarification": False,
    }
