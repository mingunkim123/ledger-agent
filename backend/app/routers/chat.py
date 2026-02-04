"""POST /chat (Step 8-3) - 자연어 → LLM 추출 → 저장 → 한 줄 응답"""
from datetime import date
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from google.genai.errors import ClientError
from openai import APIError as OpenAIAPIError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ChatRequest
from app.services.audit import log_audit
from app.services.idempotency import get_cached_tx_id, save_idempotency
from app.services.normalizer import normalize_amount, normalize_category, normalize_date
from app.services.orchestrator import extract_transaction
from app.services.simple_parser import parse_simple_expense
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
    # LLM 추출 (앱에서 선택한 provider 사용, 없으면 서버 기본값)
    result = None
    try:
        result = await extract_transaction(
            body.user_id,
            body.message,
            provider_override=body.llm_provider,
        )
    except (ClientError, OpenAIAPIError) as e:
        code = getattr(e, "code", None) or getattr(e, "status_code", None)
        err_str = str(e).lower()
        if code == 400 or "400" in str(e) or "bad request" in err_str:
            return {
                "reply": "LLM 요청 형식 오류예요. .env에서 GROK_MODEL=grok-4, API 키가 올바른지 확인해 주세요.",
                "tx_id": None,
                "undo_token": None,
                "needs_clarification": False,
            }
        if code == 429 or "429" in str(e) or "rate" in err_str or "quota" in err_str:
            fallback = parse_simple_expense(body.message)
            if fallback:
                fallback["user_id"] = body.user_id
                fallback["source_text"] = body.message
                result = {"action": "create", "args": fallback}
            else:
                return {
                    "reply": "무료 할당량을 초과했어요. 1분 뒤에 다시 시도해 주세요.",
                    "tx_id": None,
                    "undo_token": None,
                    "needs_clarification": False,
                }
        if code == 403 or "403" in str(e) or "permission" in str(e).lower() or "auth" in str(e).lower():
            return {
                "reply": "API 키를 확인해 주세요. (Gemini: aistudio.google.com, Groq: console.groq.com, Grok: x.ai)",
                "tx_id": None,
                "undo_token": None,
                "needs_clarification": False,
            }
        if result is None:
            msg = getattr(e, "message", None) or str(e)
            raise HTTPException(status_code=502, detail=f"LLM 오류: {msg}")

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
            "occurred_date": occurred_date,
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
