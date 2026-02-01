"""POST/GET /transactions (Step 5에서 구현)"""
from fastapi import APIRouter, Query

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("")
async def create_transaction():
    return {"tx_id": None, "message": "Step 5에서 구현 예정"}


@router.get("")
async def list_transactions(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    category: str | None = None,
):
    return {"transactions": [], "message": "Step 5에서 구현 예정"}
