"""
test_serializers.py — 입력 검증 Serializer 테스트

Serializer는 "문 앞의 보안 검색대" 역할입니다.
이상한 데이터가 들어오면 여기서 걸러야 합니다.

실행: pytest tests/test_serializers.py -v
"""

import pytest

from accounts.serializers import RegisterSerializer
from ledger.serializers import (
    ChatRequestSerializer,
    CreateTransactionSerializer,
    SummaryQuerySerializer,
    TransactionListQuerySerializer,
)


# ══════════════════════════════════════════
# ChatRequestSerializer
# ══════════════════════════════════════════


class TestChatRequestSerializer:
    """POST /chat/ 요청 데이터 검증."""

    def test_정상_입력(self):
        data = {"message": "점심 김치찌개 8000원"}
        serializer = ChatRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_message_없으면_에러(self):
        serializer = ChatRequestSerializer(data={})
        assert not serializer.is_valid()
        assert "message" in serializer.errors

    def test_선택필드_기본값(self):
        data = {"message": "테스트"}
        serializer = ChatRequestSerializer(data=data)
        serializer.is_valid()
        assert serializer.validated_data["session_id"] is None
        assert serializer.validated_data["idem_key"] is None
        assert serializer.validated_data["llm_provider"] is None


# ══════════════════════════════════════════
# CreateTransactionSerializer
# ══════════════════════════════════════════


class TestCreateTransactionSerializer:
    """POST /transactions/ 요청 데이터 검증."""

    def test_정상_입력(self):
        data = {
            "occurred_date": "2026-02-13",
            "type": "expense",
            "amount": "8000",
            "category": "식비",
        }
        serializer = CreateTransactionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_필수필드_누락(self):
        """occurred_date, type, amount, category는 필수"""
        serializer = CreateTransactionSerializer(data={})
        assert not serializer.is_valid()
        # 4개 필수 필드 모두 에러
        assert "occurred_date" in serializer.errors
        assert "type" in serializer.errors
        assert "amount" in serializer.errors
        assert "category" in serializer.errors

    def test_잘못된_type은_에러(self):
        data = {
            "occurred_date": "2026-02-13",
            "type": "invalid",
            "amount": "8000",
            "category": "식비",
        }
        serializer = CreateTransactionSerializer(data=data)
        assert not serializer.is_valid()
        assert "type" in serializer.errors


# ══════════════════════════════════════════
# SummaryQuerySerializer
# ══════════════════════════════════════════


class TestSummaryQuerySerializer:
    """GET /summary/ 쿼리 파라미터 검증."""

    def test_month_정상(self):
        serializer = SummaryQuerySerializer(data={"month": "2026-02"})
        assert serializer.is_valid(), serializer.errors

    def test_month_형식_오류(self):
        serializer = SummaryQuerySerializer(data={"month": "2026-2"})
        assert not serializer.is_valid()

    def test_month_없고_from_to_있으면_정상(self):
        data = {"from_date": "2026-02-01", "to_date": "2026-02-28"}
        serializer = SummaryQuerySerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_아무것도_없으면_에러(self):
        serializer = SummaryQuerySerializer(data={})
        assert not serializer.is_valid()


# ══════════════════════════════════════════
# RegisterSerializer (accounts)
# ══════════════════════════════════════════


@pytest.mark.django_db
class TestRegisterSerializer:
    """회원가입 입력 검증."""

    def test_정상_회원가입(self):
        data = {
            "username": "newuser",
            "password": "strongpass1!",
            "password2": "strongpass1!",
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_비밀번호_불일치(self):
        data = {
            "username": "newuser",
            "password": "strongpass1!",
            "password2": "differentpass!",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password2" in serializer.errors

    def test_짧은_비밀번호(self):
        data = {"username": "usr", "password": "short", "password2": "short"}
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_짧은_아이디(self):
        data = {
            "username": "ab",
            "password": "strongpass1!",
            "password2": "strongpass1!",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "username" in serializer.errors
