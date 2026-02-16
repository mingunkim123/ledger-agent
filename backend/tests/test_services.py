"""
test_services.py — 비즈니스 로직 테스트 (DB 사용, Redis Mock)

서비스 계층은 "실제 비즈니스 규칙"이 담긴 곳입니다.
여기서 문제가 나면 사용자에게 직접 영향이 갑니다.

핵심 개념: @pytest.mark.django_db
    이 데코레이터가 붙은 테스트만 DB에 접근할 수 있습니다.
    각 테스트는 독립적인 트랜잭션으로 격리되어,
    한 테스트의 데이터가 다른 테스트에 영향을 주지 않습니다.

실행: pytest tests/test_services.py -v
"""

from datetime import date
from unittest.mock import patch

import pytest

from ledger.models import Transaction
from ledger.services.transaction import TransactionService


@pytest.mark.django_db
class TestCreateTransaction:
    """TransactionService.create_transaction() 테스트."""

    # Redis 호출을 Mock으로 대체 — 실제 Redis 없이 테스트 가능
    @patch("ledger.services.transaction.save_undo_token")
    @patch("ledger.services.transaction.log_audit")
    @patch("ledger.services.transaction.get_cached_tx_id", return_value=None)
    def test_정상_거래_생성(self, mock_cache, mock_audit, mock_undo, user):
        """거래가 DB에 저장되고 올바른 결과가 반환되는지 확인."""
        result = TransactionService.create_transaction(
            user_id=str(user.id),
            args={
                "occurred_date": "2026-02-13",
                "type": "expense",
                "amount": "8000",
                "category": "식비",
                "subcategory": "식사",
            },
        )

        # 반환값 검증
        assert result["cached"] is False
        assert result["amount"] == 8000
        assert result["category"] == "식비"
        assert "tx_id" in result
        assert "undo_token" in result

        # DB에 실제로 저장되었는지 확인
        tx = Transaction.objects.get(tx_id=result["tx_id"])
        assert tx.amount == 8000
        assert tx.user_id == str(user.id)

    @patch("ledger.services.transaction.save_undo_token")
    @patch("ledger.services.transaction.log_audit")
    @patch("ledger.services.transaction.get_cached_tx_id", return_value=None)
    def test_금액_0이하면_에러(self, mock_cache, mock_audit, mock_undo, user):
        """금액이 0이하면 ValueError가 발생해야 합니다."""
        with pytest.raises(ValueError, match="금액은 0보다 커야 합니다"):
            TransactionService.create_transaction(
                user_id=str(user.id),
                args={
                    "occurred_date": "2026-02-13",
                    "type": "expense",
                    "amount": "0",
                    "category": "식비",
                },
            )

    @patch("ledger.services.transaction.save_undo_token")
    @patch("ledger.services.transaction.log_audit")
    @patch(
        "ledger.services.transaction.get_cached_tx_id", return_value="existing-tx-id"
    )
    def test_멱등성_캐시_히트(self, mock_cache, mock_audit, mock_undo, user):
        """같은 idem_key로 두 번 호출하면 캐시된 결과를 반환."""
        result = TransactionService.create_transaction(
            user_id=str(user.id),
            args={
                "occurred_date": "2026-02-13",
                "type": "expense",
                "amount": "8000",
                "category": "식비",
            },
            idem_key="unique-key-123",
        )

        assert result["cached"] is True
        assert result["tx_id"] == "existing-tx-id"

    @patch("ledger.services.transaction.save_undo_token")
    @patch("ledger.services.transaction.log_audit")
    @patch("ledger.services.transaction.get_cached_tx_id", return_value=None)
    def test_만원_단위_금액_정규화(self, mock_cache, mock_audit, mock_undo, user):
        """'2.3만' 같은 입력이 23000으로 변환되는지 E2E 확인."""
        result = TransactionService.create_transaction(
            user_id=str(user.id),
            args={
                "occurred_date": "2026-02-13",
                "type": "expense",
                "amount": "2.3만",
                "category": "식비",
            },
        )

        assert result["amount"] == 23000


@pytest.mark.django_db
class TestListTransactions:
    """TransactionService.list_transactions() 테스트."""

    def test_빈_목록(self, user):
        """거래가 없으면 빈 QuerySet 반환."""
        result = TransactionService.list_transactions(user_id=str(user.id))
        assert result.count() == 0

    def test_본인_거래만_조회(self, user, other_user, sample_transaction):
        """다른 사용자의 거래는 보이지 않아야 합니다."""
        # sample_transaction은 user의 거래
        result = TransactionService.list_transactions(user_id=str(other_user.id))
        assert result.count() == 0

    def test_카테고리_필터링(self, user, multiple_transactions):
        """category 필터가 정상 작동하는지 확인."""
        result = TransactionService.list_transactions(
            user_id=str(user.id), category="식비"
        )
        assert result.count() == 1
        assert result.first().category == "식비"

    def test_날짜_범위_필터링(self, user, multiple_transactions):
        """from_date ~ to_date 범위 필터링."""
        result = TransactionService.list_transactions(
            user_id=str(user.id),
            from_date=date(2026, 2, 11),
            to_date=date(2026, 2, 12),
        )
        assert result.count() == 2


@pytest.mark.django_db
class TestGetSummary:
    """TransactionService.get_summary() 테스트."""

    def test_월별_요약(self, user, multiple_transactions):
        """2026-02 요약: expense만 합산, income은 제외."""
        result = TransactionService.get_summary(user_id=str(user.id), month="2026-02")

        # income 100,000은 제외
        assert result["total"] == 50000  # 5000 + 15000 + 30000
        assert "식비" in result["by_category"]
        assert "교통" in result["by_category"]
        assert "쇼핑" in result["by_category"]
        assert "급여" not in result["by_category"]  # income은 제외

    def test_빈_월은_total_0(self, user):
        """거래가 없는 달은 total=0."""
        result = TransactionService.get_summary(user_id=str(user.id), month="2025-01")
        assert result["total"] == 0
        assert result["by_category"] == {}
