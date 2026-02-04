"""LLM 없이 단순 패턴으로 지출 추출 (429 폴백용).
예: "오늘 커피 5000원", "점심 12000", "버스 1500원"
"""
import re
from datetime import date
from typing import Any


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
    """
    단순 지출 문장에서 (날짜, 금액, 항목/카테고리) 추출.
    성공 시: {"occurred_date": "YYYY-MM-DD", "type": "expense", "amount": int, "category": str, "merchant": str|None}
    실패 시: None
    """
    msg = (message or "").strip()
    if len(msg) < 2:
        return None

    # 오늘/어제/날짜
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

    # 금액 부분 제거해서 항목/카테고리 추출
    rest = re.sub(r"\d+(?:\.\d+)?\s*만|\d+\s*천|\d{1,3}(?:,\d{3})*\s*원?|\d+\s*원?", "", msg)
    rest = re.sub(r"\s+", " ", rest).strip()
    if not rest:
        rest = "기타"

    # 짧은 단어를 카테고리로 매핑
    category_map = {
        "커피": "식비", "카페": "식비", "점심": "식비", "저녁": "식비", "아침": "식비",
        "식비": "식비", "밥": "식비", "버스": "교통", "지하철": "교통", "택시": "교통", "교통": "교통",
        "편의점": "쇼핑", "마트": "쇼핑", "쇼핑": "쇼핑",
    }
    category = "기타"
    for kw, cat in category_map.items():
        if kw in rest:
            category = cat
            break

    return {
        "occurred_date": occurred_date,
        "type": "expense",
        "amount": amount,
        "category": category,
        "merchant": rest if len(rest) <= 20 else rest[:20],
        "memo": None,
        "source_text": message,
    }
