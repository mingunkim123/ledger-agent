"""환경 설정 (Step 3-3) - .env 로드"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """앱 설정 - 환경변수 또는 .env에서 로드"""

    app_name: str = "가계부 에이전트"
    debug: bool = False

    # DB (Step 5에서 연결)
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/expense_db"

    # JWT (Step 4 이후 사용)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # Redis (Step 6 - Undo)
    redis_url: str = "redis://localhost:6379/0"
    undo_ttl_seconds: int = 300  # 5분

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
