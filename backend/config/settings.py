"""
Django 설정 - 가계부 에이전트
기존 FastAPI 환경변수(.env) 호환
"""

import dj_database_url
from pathlib import Path

import environ

# ── 경로 ──
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# ── django-environ ──
env = environ.Env(
    DEBUG=(bool, False),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    UNDO_TTL_SECONDS=(int, 300),
)
if ENV_FILE.exists():
    environ.Env.read_env(str(ENV_FILE))

# ── Django 기본 ──
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = ["*"]

# ── 앱 ──
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "ledger",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── DB ──
_raw_db_url = env(
    "DATABASE_URL", default="postgresql://myuser:password@localhost:5432/expense_db"
)
_db_url = _raw_db_url.replace("postgresql+asyncpg://", "postgresql://")

DATABASES = {
    "default": dj_database_url.parse(_db_url, engine="django.db.backends.postgresql"),
}

# ── Django REST Framework ──
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "UNAUTHENTICATED_USER": None,
}

# ── Redis ──
REDIS_URL = env("REDIS_URL")
UNDO_TTL_SECONDS = env("UNDO_TTL_SECONDS")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

# ── LLM 설정 (구조화) ──
LLM_PROVIDER = env("LLM_PROVIDER", default="groq")

LLM_CONFIG = {
    "ollama": {
        "base_url": env("OLLAMA_BASE_URL", default="http://localhost:11434/v1"),
        "model": env("OLLAMA_MODEL", default="llama3.2"),
    },
    "gemini": {
        "api_key": env("GEMINI_API_KEY", default=""),
        "model": env("GEMINI_MODEL", default="gemini-2.0-flash"),
    },
    "groq": {
        "api_key": env("GROQ_API_KEY", default=""),
        "model": env("GROQ_MODEL", default="llama-3.3-70b-versatile"),
    },
    "grok": {
        "api_key": env("GROK_API_KEY", default=""),
        "model": env("GROK_MODEL", default="grok-4"),
    },
}

# 하위 호환: 기존 settings.GEMINI_API_KEY 등 접근 지원
OLLAMA_BASE_URL = LLM_CONFIG["ollama"]["base_url"]
OLLAMA_MODEL = LLM_CONFIG["ollama"]["model"]
GEMINI_API_KEY = LLM_CONFIG["gemini"]["api_key"]
GEMINI_MODEL = LLM_CONFIG["gemini"]["model"]
GROQ_API_KEY = LLM_CONFIG["groq"]["api_key"]
GROQ_MODEL = LLM_CONFIG["groq"]["model"]
GROK_API_KEY = LLM_CONFIG["grok"]["api_key"]
GROK_MODEL = LLM_CONFIG["grok"]["model"]

# ── 기타 ──
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

APP_NAME = "가계부 에이전트"
