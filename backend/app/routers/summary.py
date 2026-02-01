"""GET /summary (Step 5에서 구현)"""
from fastapi import APIRouter, Query

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("")
async def get_summary(month: str = Query(..., description="YYYY-MM")):
    return {"month": month, "by_category": {}, "message": "Step 5에서 구현 예정"}
