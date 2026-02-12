"""POST /undo (Step 7-3) - 마지막 저장 취소 + 감사로그"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.undo import UndoRequest
from app.services.audit import log_audit
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

    # 삭제 전 트랜잭션 조회 (감사로그용)
    result = await session.execute(
        text("""
            SELECT tx_id, user_id, occurred_date, type, amount, currency, category, subcategory, merchant, memo, source_text, created_at, updated_at
            FROM transactions WHERE tx_id = :tx_id
        """),
        {"tx_id": str(tx_id)},
    )
    row = result.fetchone()
    if not row:
        await delete_undo_token(body.undo_token)
        raise HTTPException(status_code=404, detail="해당 트랜잭션을 찾을 수 없습니다.")

    before_snapshot = {
        "tx_id": str(row[0]),
        "user_id": row[1],
        "occurred_date": str(row[2]),
        "type": row[3],
        "amount": row[4],
        "currency": row[5],
        "category": row[6],
        "subcategory": row[7],
        "merchant": row[8],
        "memo": row[9],
        "source_text": row[10],
        "created_at": row[11].isoformat() if row[11] else None,
        "updated_at": row[12].isoformat() if row[12] else None,
    }
    user_id = row[1]

    # 감사로그: undo (삭제 전 기록)
    await log_audit(session, user_id, "undo", tx_id=tx_id, before_snapshot=before_snapshot, after_snapshot=None)

    # 트랜잭션 삭제 (idempotency_keys는 ON DELETE CASCADE로 자동 삭제)
    await session.execute(
        text("DELETE FROM transactions WHERE tx_id = :tx_id"),
        {"tx_id": str(tx_id)},
    )

    # DB 커밋 후 Redis 토큰 삭제 (1회용)
    await session.commit()
    await delete_undo_token(body.undo_token)

    return {"success": True, "tx_id": str(tx_id), "message": "저장이 취소되었습니다."}
