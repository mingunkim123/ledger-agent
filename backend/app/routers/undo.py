"""POST /undo (Step 6에서 구현)"""
from fastapi import APIRouter

router = APIRouter(prefix="/undo", tags=["undo"])


@router.post("")
async def undo():
    return {"success": False, "message": "Step 6에서 구현 예정"}
