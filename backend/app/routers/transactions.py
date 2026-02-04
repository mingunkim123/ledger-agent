"""POST/GET /transactions (Step 6-2: undo_token 추가)"""
from datetime import date
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.transaction import CreateTransactionRequest
from app.services.audit import log_audit
from app.services.idempotency import get_cached_tx_id, save_idempotency
from app.services.normalizer import normalize_amount, normalize_category, normalize_date
from app.services.undo import save_undo_token

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("")
async def create_transaction(
    body: CreateTransactionRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    POST /transactions
    idem_key 있으면 중복 요청 시 캐시된 tx_id 반환.
    date/amount/category는 서버에서 정규화 적용.
    """
    # idempotency: 캐시 확인
    if body.idem_key:
        cached = await get_cached_tx_id(session, body.user_id, body.idem_key)
        if cached:
            return {"tx_id": str(cached), "cached": True, "undo_token": None}

    # 정규화 (서버 최종 책임)
    try:
        occurred_date = normalize_date(body.occurred_date)
        amount = normalize_amount(body.amount)
        category = normalize_category(body.category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if amount <= 0:
        raise HTTPException(status_code=400, detail="금액은 0보다 커야 합니다")

    # 트랜잭션 생성
    result = await session.execute(
        text("""
            INSERT INTO transactions (user_id, occurred_date, type, amount, currency, category, merchant, memo, source_text)
            VALUES (:user_id, :occurred_date, :type, :amount, :currency, :category, :merchant, :memo, :source_text)
            RETURNING tx_id
        """),
        {
            "user_id": body.user_id,
            "occurred_date": str(occurred_date),
            "type": body.type,
            "amount": amount,
            "currency": body.currency,
            "category": category,
            "merchant": body.merchant,
            "memo": body.memo,
            "source_text": body.source_text,
        },
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="트랜잭션 생성 실패")
    tx_id = UUID(str(row[0]))

    # idempotency: 저장
    if body.idem_key:
        await save_idempotency(session, body.user_id, body.idem_key, tx_id)

    # 감사로그: create
    after_snapshot = {
        "tx_id": str(tx_id),
        "user_id": body.user_id,
        "occurred_date": str(occurred_date),
        "type": body.type,
        "amount": amount,
        "currency": body.currency,
        "category": category,
        "merchant": body.merchant,
        "memo": body.memo,
        "source_text": body.source_text,
    }
    await log_audit(session, body.user_id, "create", tx_id=tx_id, after_snapshot=after_snapshot)

    # undo_token: Redis에 TTL 저장
    undo_token = str(uuid4())
    await save_undo_token(undo_token, tx_id)

    return {"tx_id": str(tx_id), "cached": False, "undo_token": undo_token}


@router.get("")
async def list_transactions(
    user_id: str = Query(..., description="사용자 ID"),
    from_date: str | None = Query(None, alias="from", description="YYYY-MM-DD"),
    to_date: str | None = Query(None, alias="to", description="YYYY-MM-DD"),
    category: str | None = Query(None, description="카테고리 필터"),
    session: AsyncSession = Depends(get_db),
):
    """
    GET /transactions
    user_id 필수. from, to, category로 필터링.
    """
    # 동적 쿼리 구성 (asyncpg는 DATE에 date 객체 필요)
    conditions = ["user_id = :user_id"]
    params: dict = {"user_id": user_id}
    if from_date:
        conditions.append("occurred_date >= :from_date")
        params["from_date"] = date.fromisoformat(from_date)
    if to_date:
        conditions.append("occurred_date <= :to_date")
        params["to_date"] = date.fromisoformat(to_date)
    if category:
        conditions.append("category = :category")
        params["category"] = category

    where_clause = " AND ".join(conditions)
    result = await session.execute(
        text(f"""
            SELECT tx_id, user_id, occurred_date, type, amount, currency, category, merchant, memo, source_text, created_at
            FROM transactions
            WHERE {where_clause}
            ORDER BY occurred_date DESC, created_at DESC
        """),
        params,
    )
    rows = result.fetchall()
    transactions_list = [
        {
            "tx_id": str(row[0]),
            "user_id": row[1],
            "occurred_date": str(row[2]),
            "type": row[3],
            "amount": row[4],
            "currency": row[5],
            "category": row[6],
            "merchant": row[7],
            "memo": row[8],
            "source_text": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
        }
        for row in rows
    ]
    return {"transactions": transactions_list}
