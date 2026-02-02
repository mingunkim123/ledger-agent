"""
가계부 에이전트 - FastAPI 앱 (Step 4-1)
"""
from fastapi import Depends, FastAPI

from app.config import settings
from app.database import get_db
from app.routers import chat, transactions, undo, summary
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(title=settings.app_name, version="0.1.0")

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
