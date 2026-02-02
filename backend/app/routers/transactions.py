"""POST/GET /transactions (Step 4-3: idempotency 적용)"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.transaction import CreateTransactionRequest
from app.services.idempotency import get_cached_tx_id, save_idempotency

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("")
async def create_transaction(
    body: CreateTransactionRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    POST /transactions
    idem_key 있으면 중복 요청 시 캐시된 tx_id 반환.
    """
    # idempotency: 캐시 확인
    if body.idem_key:
        cached = await get_cached_tx_id(session, body.user_id, body.idem_key)
        if cached:
            return {"tx_id": str(cached), "cached": True}

    # 트랜잭션 생성
    result = await session.execute(
        text("""
            INSERT INTO transactions (user_id, occurred_date, type, amount, currency, category, merchant, memo, source_text)
            VALUES (:user_id, :occurred_date, :type, :amount, :currency, :category, :merchant, :memo, :source_text)
            RETURNING tx_id
        """),
        {
            "user_id": body.user_id,
            "occurred_date": str(body.occurred_date),
            "type": body.type,
            "amount": body.amount,
            "currency": body.currency,
            "category": body.category,
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

    return {"tx_id": str(tx_id), "cached": False}


@router.get("")
async def list_transactions(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    category: str | None = None,
):
    return {"transactions": [], "message": "Step 5에서 구현 예정"}
