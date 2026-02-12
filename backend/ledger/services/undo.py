"""Undo 토큰 서비스 - Redis TTL 저장/조회"""

from uuid import UUID

from django.conf import settings
from django_redis import get_redis_connection

REDIS_KEY_PREFIX = "undo:"


def save_undo_token(
    undo_token: str, tx_id: UUID, ttl_seconds: int | None = None
) -> None:
    """Redis에 undo_token → tx_id 저장 (TTL 적용)."""
    ttl = ttl_seconds or settings.UNDO_TTL_SECONDS
    redis = get_redis_connection("default")
    key = f"{REDIS_KEY_PREFIX}{undo_token}"
    redis.set(key, str(tx_id), ex=ttl)


def get_tx_id_from_undo_token(undo_token: str) -> UUID | None:
    """Redis에서 undo_token으로 tx_id 조회."""
    redis = get_redis_connection("default")
    key = f"{REDIS_KEY_PREFIX}{undo_token}"
    value = redis.get(key)
    if value is None:
        return None
    # django-redis returns bytes by default
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return UUID(value)


def delete_undo_token(undo_token: str) -> None:
    """Redis에서 undo_token 삭제 (1회용, 재사용 방지)."""
    redis = get_redis_connection("default")
    key = f"{REDIS_KEY_PREFIX}{undo_token}"
    redis.delete(key)
