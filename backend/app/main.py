"""
가계부 에이전트 - FastAPI 앱 (Step 3-3)
"""
from fastapi import FastAPI

from app.config import settings
from app.routers import chat, transactions, undo, summary

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
