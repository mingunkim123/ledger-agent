"""
test_api_ledger.py — 거래 CRUD + 헬스체크 API 통합 테스트

이 테스트들은 JWT 인증이 올바르게 작동하는지도 함께 검증합니다.
- 인증 없이 접근 → 401
- 인증 후 접근 → 200

실행: pytest tests/test_api_ledger.py -v
"""

from unittest.mock import patch

import pytest
from rest_framework import status


# ══════════════════════════════════════════
# 헬스체크 (인증 불필요)
# ══════════════════════════════════════════


@pytest.mark.django_db
class TestHealthAPI:
    """GET /health/ — 인증 없이 접근 가능."""

    def test_헬스체크_200(self, unauthenticated_client):
        response = unauthenticated_client.get("/health/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"

    def test_루트_200(self, unauthenticated_client):
        response = unauthenticated_client.get("/")
        assert response.status_code == status.HTTP_200_OK


# ══════════════════════════════════════════
# 인증 필수 확인
# ══════════════════════════════════════════


@pytest.mark.django_db
class TestAuthRequired:
    """인증 없이 ledger API 호출 → 401."""

    def test_transactions_인증_필수(self, unauthenticated_client):
        response = unauthenticated_client.get("/api/v1/transactions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_chat_인증_필수(self, unauthenticated_client):
        response = unauthenticated_client.post(
            "/api/v1/chat/", {"message": "테스트"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_summary_인증_필수(self, unauthenticated_client):
        response = unauthenticated_client.get("/api/v1/summary/?month=2026-02")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ══════════════════════════════════════════
# 거래 생성 API
# ══════════════════════════════════════════


@pytest.mark.django_db
class TestTransactionCreateAPI:
    """POST /api/v1/transactions/ — 거래 생성."""

    URL = "/api/v1/transactions/"

    @patch("ledger.services.transaction.save_undo_token")
    @patch("ledger.services.transaction.log_audit")
    @patch("ledger.services.transaction.get_cached_tx_id", return_value=None)
    def test_정상_거래_생성(self, mock_cache, mock_audit, mock_undo, api_client):
        response = api_client.post(
            self.URL,
            {
                "occurred_date": "2026-02-13",
                "type": "expense",
                "amount": "8000",
                "category": "식비",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "tx_id" in response.data
        assert response.data["cached"] is False

    def test_필수필드_누락_400(self, api_client):
        response = api_client.post(self.URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ══════════════════════════════════════════
# 거래 조회 API
# ══════════════════════════════════════════


@pytest.mark.django_db
class TestTransactionListAPI:
    """GET /api/v1/transactions/ — 거래 조회."""

    URL = "/api/v1/transactions/"

    def test_빈_목록_조회(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["transactions"] == []

    def test_거래_있으면_조회(self, api_client, sample_transaction):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["transactions"]) == 1
        assert response.data["transactions"][0]["amount"] == 8000
