"""Redis 연결 (Step 6-1) - Undo 토큰 TTL 저장용"""
from redis.asyncio import Redis as RedisClient

from app.config import settings

# Redis 클라이언트 (Step 6-2에서 사용)
_redis: RedisClient | None = None


async def get_redis() -> RedisClient:
    """Redis 클라이언트 반환. 앱 시작 시 초기화됨."""
    if _redis is None:
        raise RuntimeError("Redis가 초기화되지 않았습니다. 앱 시작 시 init_redis() 호출 필요.")
    return _redis


async def init_redis() -> None:
    """앱 시작 시 Redis 연결 초기화"""
    global _redis
    _redis = RedisClient.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """앱 종료 시 Redis 연결 종료"""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
