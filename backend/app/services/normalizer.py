"""정규화 헬퍼 (Step 5-1) - 날짜/금액/카테고리 서버 규칙"""
import re
from datetime import date

# 고정 카테고리 세트 (설계 규칙)
CATEGORIES = frozenset(
    {"식비", "카페", "교통", "쇼핑", "구독", "생활", "의료", "교육", "여행", "기타"}
)


def normalize_date(raw: str | date, reference: date | None = None) -> date:
    """
    날짜 정규화.
    - date 객체면 그대로 반환
    - "YYYY-MM-DD" → 파싱
    - "M/D", "M월 D일" → 가장 최근 해당 날짜 (reference 기준)
    """
    ref = reference or date.today()
    if isinstance(raw, date):
        return raw
    s = str(raw).strip()

    # YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # M/D 또는 M-D
    m = re.match(r"^(\d{1,2})[/\-](\d{1,2})$", s)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        return _most_recent_date(ref, month, day)

    # M월 D일
    m = re.match(r"^(\d{1,2})월\s*(\d{1,2})일?$", s)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        return _most_recent_date(ref, month, day)

    raise ValueError(f"날짜 형식 인식 불가: {s}")


def _most_recent_date(ref: date, month: int, day: int) -> date:
    """가장 최근의 (month, day) 날짜. ref 기준."""
    # 올해 시도
    try:
        d = date(ref.year, month, day)
        if d <= ref:
            return d
    except ValueError:
        pass
    # 작년 시도 (12/31 같은 경우)
    try:
        return date(ref.year - 1, month, day)
    except ValueError:
        raise ValueError(f"유효하지 않은 날짜: {month}월 {day}일")


def normalize_amount(raw: str | int) -> int:
    """
    금액 정규화 → KRW 정수.
    - "23000", "23,000", "23,000원" → 23000
    - "2.3만" → 23000
    """
    if isinstance(raw, int):
        return raw if raw > 0 else 0
    s = str(raw).strip().replace(",", "").replace(" ", "")

    # "2.3만", "2만", "1.5만원"
    m = re.match(r"^(\d+(?:\.\d+)?)\s*만\s*원?$", s)
    if m:
        return int(float(m.group(1)) * 10_000)

    # "23000", "23000원"
    m = re.match(r"^(\d+)\s*원?$", s)
    if m:
        return int(m.group(1))

    # 숫자만
    m = re.match(r"^(\d+)$", s)
    if m:
        return int(m.group(1))

    raise ValueError(f"금액 형식 인식 불가: {raw}")


def normalize_category(raw: str) -> str:
    """
    카테고리 정규화.
    고정 세트에 있으면 반환, 없으면 "기타".
    """
    s = str(raw).strip()
    return s if s in CATEGORIES else "기타"
