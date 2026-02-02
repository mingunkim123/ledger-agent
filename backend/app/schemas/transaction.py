"""트랜잭션 요청/응답 스키마 (Step 4-3)"""
from datetime import date

from pydantic import BaseModel, Field


class CreateTransactionRequest(BaseModel):
    """POST /transactions 요청"""

    user_id: str
    occurred_date: date
    type: str = Field(..., pattern="^(expense|income)$")
    amount: int = Field(..., gt=0)
    category: str
    currency: str = "KRW"
    merchant: str | None = None
    memo: str | None = None
    source_text: str | None = None
    idem_key: str | None = None  # 중복 방지용 (선택)
