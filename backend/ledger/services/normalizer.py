"""정규화 헬퍼 - 날짜/금액/카테고리/세부카테고리 서버 규칙"""

import re
from datetime import date

# 상위 카테고리 세트
CATEGORIES = frozenset({"식비", "교통", "쇼핑", "문화", "의료", "교육", "통신", "기타"})

# 과거/동의어 카테고리 입력 호환
CATEGORY_ALIASES = {
    "카페": "식비",
    "구독": "통신",
    "생활": "기타",
    "여행": "문화",
    "식사": "식비",
}

# 프롬프트/가맹점 키워드 기반 기본 분류 규칙
_CATEGORY_SUBCATEGORY_RULES: tuple[tuple[tuple[str, ...], tuple[str, str]], ...] = (
    (
        (
            "점심",
            "저녁",
            "아침",
            "식당",
            "배달",
            "치킨",
            "피자",
            "햄버거",
            "분식",
            "밥",
        ),
        ("식비", "식사"),
    ),
    (
        ("커피", "카페", "스타벅스", "투썸", "이디야", "메가커피", "컴포즈"),
        ("식비", "카페"),
    ),
    (
        ("버스", "지하철", "택시", "주유", "주차", "기차", "ktx", "교통"),
        ("교통", "이동"),
    ),
    (
        ("쿠팡", "네이버쇼핑", "마트", "편의점", "다이소", "쇼핑", "의류", "신발"),
        ("쇼핑", "생필품"),
    ),
    (
        ("영화", "넷플릭스", "디즈니", "유튜브", "콘서트", "전시", "게임", "여행"),
        ("문화", "여가"),
    ),
    (
        ("병원", "약국", "치과", "진료", "약", "의료"),
        ("의료", "진료/약제"),
    ),
    (
        ("학원", "교재", "강의", "수업", "책", "교육"),
        ("교육", "학습"),
    ),
    (
        ("통신비", "휴대폰", "요금제", "인터넷", "구독", "멜론", "스포티파이"),
        ("통신", "통신/구독"),
    ),
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
    try:
        d = date(ref.year, month, day)
        if d <= ref:
            return d
    except ValueError:
        pass
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
    """카테고리 정규화."""
    s = str(raw or "").strip()
    if not s:
        return "기타"
    if s in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[s]
    for keywords, (category, _) in _CATEGORY_SUBCATEGORY_RULES:
        if any(keyword in s for keyword in keywords):
            return category
    return s if s in CATEGORIES else "기타"


def normalize_subcategory(raw: str | None) -> str:
    """세부 카테고리 정규화. 비어있으면 '기타'."""
    s = str(raw or "").strip()
    if not s:
        return "기타"
    return s[:30]


def infer_category_subcategory(
    source_text: str | None = None,
    merchant: str | None = None,
) -> tuple[str, str]:
    """자유 입력 문장/가맹점에서 상위/세부 카테고리를 추론."""
    raw = " ".join(v for v in [source_text, merchant] if v).strip()
    if not raw:
        return "기타", "기타"

    normalized = raw.lower().replace(" ", "")
    for keywords, (category, subcategory) in _CATEGORY_SUBCATEGORY_RULES:
        if any(keyword.replace(" ", "") in normalized for keyword in keywords):
            return category, subcategory

    if merchant and merchant.strip():
        return "기타", normalize_subcategory(merchant)
    return "기타", "기타"


def resolve_category_subcategory(
    category: str | None,
    subcategory: str | None,
    source_text: str | None = None,
    merchant: str | None = None,
) -> tuple[str, str]:
    """입력값 + 추론 결과를 합쳐 카테고리/세부 카테고리를 최종 결정."""
    inferred_category, inferred_subcategory = infer_category_subcategory(
        source_text=source_text,
        merchant=merchant,
    )
    normalized_category = normalize_category(category or inferred_category)
    if normalized_category == "기타" and inferred_category != "기타":
        normalized_category = inferred_category

    selected_subcategory = subcategory
    if not str(selected_subcategory or "").strip():
        if normalized_category == inferred_category:
            selected_subcategory = inferred_subcategory
        elif merchant and merchant.strip():
            selected_subcategory = merchant
        else:
            selected_subcategory = "기타"

    return normalized_category, normalize_subcategory(selected_subcategory)
