"""
test_api_accounts.py — 회원가입/로그인 API 통합 테스트

통합 테스트는 "실제 HTTP 요청 → 응답" 을 검증합니다.
DRF의 APIClient를 사용하면 실제 서버를 띄우지 않고도
HTTP 요청을 시뮬레이션할 수 있습니다.

실행: pytest tests/test_api_accounts.py -v
"""

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestRegisterAPI:
    """POST /api/v1/accounts/register/ — 회원가입."""

    URL = "/api/v1/accounts/register/"

    def test_정상_회원가입(self, unauthenticated_client):
        response = unauthenticated_client.post(
            self.URL,
            {
                "username": "newuser",
                "password": "strongpass1!",
                "password2": "strongpass1!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "newuser"
        assert "message" in response.data

    def test_중복_아이디(self, unauthenticated_client, user):
        """이미 존재하는 username으로 가입 시도 → 400."""
        response = unauthenticated_client.post(
            self.URL,
            {
                "username": "testuser",  # user fixture가 이미 생성한 아이디
                "password": "strongpass1!",
                "password2": "strongpass1!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_비밀번호_불일치(self, unauthenticated_client):
        response = unauthenticated_client.post(
            self.URL,
            {
                "username": "newuser",
                "password": "strongpass1!",
                "password2": "wrongpass!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginAPI:
    """POST /api/v1/accounts/login/ — 로그인(토큰 발급)."""

    URL = "/api/v1/accounts/login/"

    def test_정상_로그인(self, unauthenticated_client, user):
        response = unauthenticated_client.post(
            self.URL,
            {"username": "testuser", "password": "testpass123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_잘못된_비밀번호(self, unauthenticated_client, user):
        response = unauthenticated_client.post(
            self.URL,
            {"username": "testuser", "password": "wrongpass!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_존재하지_않는_유저(self, unauthenticated_client):
        response = unauthenticated_client.post(
            self.URL,
            {"username": "ghost", "password": "testpass123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
