"""Undo 토큰 서비스 (Step 6-2) - Redis TTL 저장/조회"""
from uuid import UUID

from app.config import settings
from app.redis_client import get_redis


REDIS_KEY_PREFIX = "undo:"


async def save_undo_token(undo_token: str, tx_id: UUID, ttl_seconds: int | None = None) -> None:
    """
    Redis에 undo_token → tx_id 저장 (TTL 적용).
    TTL 만료 후 자동 삭제.
    """
    ttl = ttl_seconds or settings.undo_ttl_seconds
    redis = await get_redis()
    key = f"{REDIS_KEY_PREFIX}{undo_token}"
    await redis.set(key, str(tx_id), ex=ttl)


async def get_tx_id_from_undo_token(undo_token: str) -> UUID | None:
    """
    Redis에서 undo_token으로 tx_id 조회.
    있으면 반환, 없으면 None (만료됐거나 잘못된 토큰).
    """
    redis = await get_redis()
    key = f"{REDIS_KEY_PREFIX}{undo_token}"
    value = await redis.get(key)
    if value is None:
        return None
    return UUID(value)


async def delete_undo_token(undo_token: str) -> None:
    """Redis에서 undo_token 삭제 (1회용, 재사용 방지)"""
    redis = await get_redis()
    key = f"{REDIS_KEY_PREFIX}{undo_token}"
    await redis.delete(key)
