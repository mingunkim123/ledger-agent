"""POST /undo (Step 6-3) - 마지막 저장 취소"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.undo import UndoRequest
from app.services.undo import delete_undo_token, get_tx_id_from_undo_token

router = APIRouter(prefix="/undo", tags=["undo"])


@router.post("")
async def undo(
    body: UndoRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    POST /undo
    undo_token으로 해당 트랜잭션 삭제.
    토큰은 1회용 (5분 TTL).
    """
    # Redis에서 tx_id 조회
    tx_id = await get_tx_id_from_undo_token(body.undo_token)
    if tx_id is None:
        raise HTTPException(
            status_code=400,
            detail="undo_token이 만료됐거나 잘못됐습니다. 5분 이내에 다시 시도해주세요.",
        )

    # 트랜잭션 삭제 (idempotency_keys는 ON DELETE CASCADE로 자동 삭제)
    result = await session.execute(
        text("DELETE FROM transactions WHERE tx_id = :tx_id RETURNING tx_id"),
        {"tx_id": str(tx_id)},
    )
    row = result.fetchone()
    if not row:
        # 이미 삭제됐거나 존재하지 않음
        await delete_undo_token(body.undo_token)
        raise HTTPException(status_code=404, detail="해당 트랜잭션을 찾을 수 없습니다.")

    # DB 커밋 후 Redis 토큰 삭제 (1회용)
    await session.commit()
    await delete_undo_token(body.undo_token)

    return {"success": True, "tx_id": str(tx_id), "message": "저장이 취소되었습니다."}
