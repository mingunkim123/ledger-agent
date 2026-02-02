"""트랜잭션 요청/응답 스키마 (Step 5-2)"""
from datetime import date

from pydantic import BaseModel, Field


class CreateTransactionRequest(BaseModel):
    """POST /transactions 요청 - date/amount는 정규화 전 다양한 형식 허용"""

    user_id: str
    occurred_date: date | str  # "YYYY-MM-DD" 또는 "1/31", "1월 31일"
    type: str = Field(..., pattern="^(expense|income)$")
    amount: int | str  # 23000 또는 "2.3만", "23,000원"
    category: str
    currency: str = "KRW"
    merchant: str | None = None
    memo: str | None = None
    source_text: str | None = None
    idem_key: str | None = None  # 중복 방지용 (선택)
