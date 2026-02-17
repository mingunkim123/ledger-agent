import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User
from ledger.models import Transaction
import uuid


@pytest.mark.django_db
def test_transaction_permission_isolation():
    # 1. 사용자 A, B 생성
    user_a = User.objects.create_user(username="user_a", password="password123")
    user_b = User.objects.create_user(username="user_b", password="password123")

    # 2. 사용자 A로 로그인 및 토큰 발급
    client_a = APIClient()
    token_url = reverse("accounts:login")  # accounts 앱의 login URL
    resp_a = client_a.post(
        token_url, {"username": "user_a", "password": "password123"}, format="json"
    )
    token_a = resp_a.data["access"]
    client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")

    # 3. 사용자 B로 로그인 및 토큰 발급
    client_b = APIClient()
    resp_b = client_b.post(
        token_url, {"username": "user_b", "password": "password123"}, format="json"
    )
    token_b = resp_b.data["access"]
    client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")

    # 4. A가 Transaction 생성
    tx_data = {
        "amount": 10000,
        "category": "Food",
        "occurred_date": "2024-01-01",
        "type": "expense",
        "idem_key": str(uuid.uuid4()),
    }
    create_url = reverse("ledger:transactions")  # ledger 앱의 transactions URL
    resp_create = client_a.post(create_url, tx_data, format="json")
    assert resp_create.status_code == 200  # or 201 based on view
    tx_id_a = resp_create.data["tx_id"]

    # 5. B가 A의 Transaction 조회 시도 (목록 조회) -> 안 보여야 함
    resp_list_b = client_b.get(create_url)
    assert resp_list_b.status_code == 200
    # B의 목록에는 A의 데이터가 없어야 함
    assert len(resp_list_b.data["transactions"]) == 0

    # 6. A가 본인 목록 조회 -> 보여야 함
    resp_list_a = client_a.get(create_url)
    assert resp_list_a.status_code == 200
    assert len(resp_list_a.data["transactions"]) == 1
    assert resp_list_a.data["transactions"][0]["tx_id"] == tx_id_a

    # (Optional) Detail View 권한 테스트는 현재 View에 Detail 구현이 없어서 생략
    # 만약 Detail View가 있다면 client_b.get(detail_url) -> 403 or 404 확인
