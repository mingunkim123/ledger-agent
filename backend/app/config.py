"""환경 설정 - .env 로드"""
from pathlib import Path

from pydantic_settings import BaseSettings

# 실행 경로와 무관하게 항상 backend/.env 로드
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """앱 설정 - 환경변수 또는 .env에서 로드"""

    app_name: str = "가계부 에이전트"
    debug: bool = False

    # DB
    database_url: str = "postgresql+asyncpg://myuser:password@localhost:5432/expense_db"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # Redis (Undo 토큰 TTL 등)
    redis_url: str = "redis://localhost:6379/0"
    undo_ttl_seconds: int = 300

    # LLM: ollama(로컬 GPU) | gemini | groq | grok
    llm_provider: str = "groq"

    # Ollama - 로컬 GPU 사용, API 키 불필요 (https://ollama.com)
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Grok (xAI)
    grok_api_key: str = ""
    grok_model: str = "grok-4"

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
