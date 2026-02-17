"""TransactionQueryService — 거래 조회, 검색, 통계 (Read)"""

import calendar
from datetime import date

from django.db.models import Sum

from ledger.models import Transaction


class TransactionQueryService:
    """
    거래 조회(Read)를 담당하는 서비스.
    CQRS 패턴의 Query 역할.
    """

    @staticmethod
    def list_transactions(
        user_id: str,
        from_date=None,
        to_date=None,
        category: str | None = None,
    ):
        """
        거래 목록 조회 (필터링 적용).
        Returns: QuerySet[Transaction]
        """
        qs = Transaction.objects.filter(user_id=user_id)
        if from_date:
            qs = qs.filter(occurred_date__gte=from_date)
        if to_date:
            qs = qs.filter(occurred_date__lte=to_date)
        if category:
            qs = qs.filter(category=category)
        return qs.order_by("-occurred_date", "-created_at")

    @staticmethod
    def get_summary(
        user_id: str,
        month: str | None = None,
        from_date=None,
        to_date=None,
    ) -> dict:
        """
        기간별 카테고리별 지출 합계.
        """
        if from_date and to_date:
            label = f"{from_date} ~ {to_date}"
        elif month:
            year, m = int(month[:4]), int(month[5:7])
            from_date = date(year, m, 1)
            last_day = calendar.monthrange(year, m)[1]
            to_date = date(year, m, last_day)
            label = month
        else:
            raise ValueError("month 또는 from_date/to_date 필수")

        qs = (
            Transaction.objects.filter(
                user_id=user_id,
                type="expense",
                occurred_date__gte=from_date,
                occurred_date__lte=to_date,
            )
            .values("category")
            .annotate(cat_total=Sum("amount"))
            .order_by("-cat_total")
        )

        by_category = {row["category"]: row["cat_total"] for row in qs}
        total = sum(by_category.values())

        return {"label": label, "total": total, "by_category": by_category}

    @staticmethod
    def search_transactions(
        user_id: str,
        keyword: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        category: str | None = None,
    ) -> list[dict]:
        """
        LLM용 거래 검색.
        Returns:
            list[dict]: 검색된 거래 내역 (최대 20개)
        """
        qs = Transaction.objects.filter(user_id=user_id)

        if start_date:
            qs = qs.filter(occurred_date__gte=start_date)
        if end_date:
            qs = qs.filter(occurred_date__lte=end_date)
        if min_amount is not None:
            qs = qs.filter(amount__gte=min_amount)
        if max_amount is not None:
            qs = qs.filter(amount__lte=max_amount)
        if category and category != "기타":
            qs = qs.filter(category=category)

        if keyword:
            # merchant, category, subcategory, memo, source_text 에서 검색
            from django.db.models import Q

            qs = qs.filter(
                Q(merchant__icontains=keyword)
                | Q(category__icontains=keyword)
                | Q(subcategory__icontains=keyword)
                | Q(memo__icontains=keyword)
                | Q(source_text__icontains=keyword)
            )

        # 최신순, 최대 10개만 반환 (LLM 컨텍스트 절약)
        results = []
        for tx in qs.order_by("-occurred_date", "-created_at")[:10]:
            results.append(
                {
                    "tx_id": str(tx.tx_id),
                    "date": str(tx.occurred_date),
                    "amount": tx.amount,
                    "category": tx.category,
                    "merchant": tx.merchant or "",
                    "memo": tx.memo or "",
                }
            )
        return results
