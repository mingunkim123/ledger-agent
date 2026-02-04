"""
가계부 에이전트 - FastAPI 앱 (Step 6-1)
"""
from pathlib import Path

from dotenv import load_dotenv

# 실행 경로와 무관하게 backend/.env 로드 (DB 사용자/비밀번호 적용)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.redis_client import close_redis, init_redis
from app.routers import chat, transactions, undo, summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 Redis 연결 관리"""
    await init_redis()
    yield
    await close_redis()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# 라우터 등록
app.include_router(chat.router)
app.include_router(transactions.router)
app.include_router(undo.router)
app.include_router(summary.router)


@app.get("/")
async def root():
    return {"app": "가계부 에이전트", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_db)):
    """DB 연결 확인 (Step 4-1)"""
    result = await session.execute(text("SELECT 1"))
    result.scalar()
    return {"status": "healthy", "database": "connected"}
