"""LLM 없이 단순 패턴으로 지출 추출 (429 폴백용)."""

import re
from datetime import date
from typing import Any

from ledger.services.normalizer import infer_category_subcategory


def _today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def _parse_amount(s: str) -> int | None:
    s = s.replace(",", "").strip()
    # "1.2만" → 12000
    m = re.search(r"(\d+(?:\.\d+)?)\s*만", s)
    if m:
        return int(float(m.group(1)) * 10000)
    # "3천" → 3000
    m = re.search(r"(\d+)\s*천", s)
    if m:
        return int(m.group(1)) * 1000
    # "5000원" 또는 "12000" 또는 "12,000"
    m = re.search(r"(\d{1,3}(?:,\d{3})*|\d+)\s*원?", s)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def parse_simple_expense(message: str) -> dict[str, Any] | None:
    """단순 지출 문장에서 (날짜, 금액, 항목/카테고리) 추출."""
    msg = (message or "").strip()
    if len(msg) < 2:
        return None

    occurred_date = _today_str()
    if "어제" in msg:
        from datetime import timedelta

        d = date.today() - timedelta(days=1)
        occurred_date = d.strftime("%Y-%m-%d")
        msg = msg.replace("어제", "").strip()
    elif "오늘" in msg:
        msg = msg.replace("오늘", "").strip()

    amount = _parse_amount(msg)
    if amount is None or amount <= 0:
        return None

    rest = re.sub(
        r"\d+(?:\.\d+)?\s*만|\d+\s*천|\d{1,3}(?:,\d{3})*\s*원?|\d+\s*원?", "", msg
    )
    rest = re.sub(r"\s+", " ", rest).strip()
    if not rest:
        rest = "기타"

    category, subcategory = infer_category_subcategory(source_text=rest, merchant=rest)

    return {
        "occurred_date": occurred_date,
        "type": "expense",
        "amount": amount,
        "category": category,
        "subcategory": subcategory,
        "merchant": rest if len(rest) <= 20 else rest[:20],
        "memo": None,
        "source_text": message,
    }
