"""Redis 연결 관리 (django-redis 사용으로 대체됨)

django-redis의 get_redis_connection()을 사용하므로
별도의 초기화/종료 관리가 불필요합니다.

사용법:
    from django_redis import get_redis_connection
    redis = get_redis_connection("default")
"""
