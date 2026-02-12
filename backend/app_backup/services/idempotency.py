"""Idempotency 서비스 (Step 4-2) - 중복 요청 방지"""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_cached_tx_id(session: AsyncSession, user_id: str, idem_key: str) -> UUID | None:
    """
    idempotency_keys에서 캐시된 tx_id 조회.
    있으면 반환, 없으면 None.
    """
    result = await session.execute(
        text("SELECT tx_id FROM idempotency_keys WHERE user_id = :user_id AND idem_key = :idem_key"),
        {"user_id": user_id, "idem_key": idem_key},
    )
    row = result.fetchone()
    return UUID(str(row[0])) if row else None


async def save_idempotency(
    session: AsyncSession, user_id: str, idem_key: str, tx_id: UUID
) -> None:
    """
    idempotency_keys에 (user_id, idem_key, tx_id) 저장.
    트랜잭션 생성 직후 호출.
    """
    await session.execute(
        text("""
            INSERT INTO idempotency_keys (user_id, idem_key, tx_id)
            VALUES (:user_id, :idem_key, :tx_id)
        """),
        {"user_id": user_id, "idem_key": idem_key, "tx_id": str(tx_id)},
    )
