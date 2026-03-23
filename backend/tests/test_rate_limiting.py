import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import time

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_header(db):
    user = User.objects.create_user(username="testuser", password="password")
    token = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {str(token.access_token)}"}


@pytest.mark.django_db
def test_rate_limiting(api_client, auth_header):
    # 거래 생성 API는 분당 10회로 제한됨
    url = "/api/v1/transactions/"

    # 10회 요청 (성공해야 함)
    for _ in range(10):
        # 유효하지 않은 데이터라도 Throttling 체크는 먼저 일어남
        # 400 Bad Request가 뜨더라도 Throttling 카운트는 올라감
        response = api_client.post(url, {}, format="json", **auth_header)
        assert response.status_code != 429

    # 11번째 요청 (실패해야 함 - 429 Too Many Requests)
    response = api_client.post(url, {}, format="json", **auth_header)
    assert response.status_code == 429

    # 응답 확인
    data = response.json()
    assert "throttle" in str(data).lower() or data.get("code") == "THROTTLED"
