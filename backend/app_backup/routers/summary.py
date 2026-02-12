"""GET /summary - 월별 지출 요약 (카테고리별 합계)"""
import calendar
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("")
async def get_summary(
    month: str = Query(..., description="YYYY-MM"),
    user_id: str = Query(..., description="사용자 ID"),
    session: AsyncSession = Depends(get_db),
):
    """지정 월의 지출 합계 및 카테고리별 금액 반환."""
    year, m = int(month[:4]), int(month[5:7])
    from_date = date(year, m, 1)
    last_day = calendar.monthrange(year, m)[1]
    to_date = date(year, m, last_day)

    result = await session.execute(
        text("""
            SELECT category, COALESCE(SUM(amount), 0)::bigint AS cat_total
            FROM transactions
            WHERE user_id = :user_id AND type = 'expense'
              AND occurred_date >= :from_date AND occurred_date <= :to_date
            GROUP BY category
            ORDER BY cat_total DESC
        """),
        {"user_id": user_id, "from_date": from_date, "to_date": to_date},
    )
    rows = result.fetchall()
    by_category = {str(row[0]): int(row[1]) for row in rows}
    total = sum(by_category.values())

    return {"month": month, "total": total, "by_category": by_category}
