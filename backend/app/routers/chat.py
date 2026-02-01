"""POST /chat - 자연어 입력 (Step 8에서 구현)"""
from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat():
    return {"reply": "Step 8에서 구현 예정", "tx_id": None, "undo_token": None}
