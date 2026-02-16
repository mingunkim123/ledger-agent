"""
test_normalizer.py — 순수 함수 테스트 (DB/Redis 불필요)

이 파일의 테스트들은 DB 연결 없이 실행됩니다.
"내 코드의 가장 작은 단위가 제대로 동작하는가?"를 확인합니다.

실행: pytest tests/test_normalizer.py -v
"""

from datetime import date

import pytest

from ledger.services.normalizer import (
    infer_category_subcategory,
    normalize_amount,
    normalize_category,
    normalize_date,
    normalize_subcategory,
)


# ══════════════════════════════════════════
# normalize_amount — 금액 정규화
# ══════════════════════════════════════════


class TestNormalizeAmount:
    """다양한 금액 입력을 KRW 정수로 변환하는지 테스트."""

    def test_정수_그대로(self):
        assert normalize_amount(23000) == 23000

    def test_콤마_포함(self):
        assert normalize_amount("23,000") == 23000

    def test_원_접미사(self):
        assert normalize_amount("23000원") == 23000

    def test_콤마_원_같이(self):
        assert normalize_amount("23,000원") == 23000

    def test_만_단위(self):
        assert normalize_amount("2.3만") == 23000

    def test_만원_단위(self):
        assert normalize_amount("2.3만원") == 23000

    def test_정수_만(self):
        assert normalize_amount("2만") == 20000

    def test_공백_포함(self):
        assert normalize_amount(" 8000 ") == 8000

    def test_음수_정수면_0(self):
        assert normalize_amount(-5000) == 0

    def test_인식불가_형식은_에러(self):
        with pytest.raises(ValueError):
            normalize_amount("abc")


# ══════════════════════════════════════════
# normalize_date — 날짜 정규화
# ══════════════════════════════════════════


class TestNormalizeDate:
    """다양한 날짜 입력을 date 객체로 변환하는지 테스트."""

    # 테스트 기준일: 2026년 2월 15일로 고정
    REF = date(2026, 2, 15)

    def test_ISO_포맷(self):
        result = normalize_date("2026-02-13", self.REF)
        assert result == date(2026, 2, 13)

    def test_슬래시_포맷(self):
        result = normalize_date("2/13", self.REF)
        assert result == date(2026, 2, 13)

    def test_한국어_포맷(self):
        result = normalize_date("2월 13일", self.REF)
        assert result == date(2026, 2, 13)

    def test_date_객체_그대로(self):
        d = date(2026, 1, 1)
        assert normalize_date(d) == d

    def test_미래_날짜는_작년으로(self):
        """3월 1일인데 기준이 2월 15일이면 → 작년 3월 1일"""
        result = normalize_date("3/1", self.REF)
        assert result == date(2025, 3, 1)

    def test_인식불가는_에러(self):
        with pytest.raises(ValueError):
            normalize_date("모레", self.REF)


# ══════════════════════════════════════════
# normalize_category — 카테고리 정규화
# ══════════════════════════════════════════


class TestNormalizeCategory:
    """동의어 매핑과 키워드 기반 분류 테스트."""

    def test_동의어_카페는_식비(self):
        assert normalize_category("카페") == "식비"

    def test_동의어_구독은_통신(self):
        assert normalize_category("구독") == "통신"

    def test_정규_카테고리_그대로(self):
        assert normalize_category("교통") == "교통"

    def test_빈값은_기타(self):
        assert normalize_category("") == "기타"

    def test_None은_기타(self):
        assert normalize_category(None) == "기타"

    def test_알수없는값은_기타(self):
        assert normalize_category("외계인") == "외계인"


# ══════════════════════════════════════════
# normalize_subcategory — 세부 카테고리 정규화
# ══════════════════════════════════════════


class TestNormalizeSubcategory:
    """세부 카테고리 정규화 테스트."""

    def test_빈값은_기타(self):
        assert normalize_subcategory("") == "기타"

    def test_None은_기타(self):
        assert normalize_subcategory(None) == "기타"

    def test_최대_30자_잘림(self):
        long_text = "가" * 50
        assert len(normalize_subcategory(long_text)) == 30


# ══════════════════════════════════════════
# infer_category_subcategory — 키워드 추론
# ══════════════════════════════════════════


class TestInferCategorySubcategory:
    """자유 입력 문장에서 카테고리를 추론하는지 테스트."""

    def test_커피_키워드면_식비_카페(self):
        cat, sub = infer_category_subcategory(source_text="스타벅스 아메리카노")
        assert cat == "식비"
        assert sub == "카페"

    def test_택시_키워드면_교통(self):
        cat, sub = infer_category_subcategory(source_text="택시비")
        assert cat == "교통"

    def test_점심_키워드면_식비_식사(self):
        cat, sub = infer_category_subcategory(source_text="점심 김치찌개")
        assert cat == "식비"
        assert sub == "식사"

    def test_빈_입력이면_기타(self):
        cat, sub = infer_category_subcategory()
        assert cat == "기타"
        assert sub == "기타"

    def test_가맹점만_있으면_기타_가맹점명(self):
        cat, sub = infer_category_subcategory(merchant="알수없는가게")
        assert cat == "기타"
        assert sub == "알수없는가게"
