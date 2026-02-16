"""
공통 Fixtures — 모든 테스트에서 사용하는 공유 데이터.

Fixture란?
    테스트 실행 전에 미리 준비해두는 "재료"입니다.
    예: 테스트용 유저, 인증된 API 클라이언트, 샘플 거래 데이터 등.
    @pytest.fixture 데코레이터를 붙이면 pytest가 자동으로 주입해줍니다.
"""

# ── ROS2 플러그인 충돌 방지 ──
# 시스템에 설치된 ROS2의 launch_testing이 pytest 플러그인으로 등록되어 있어 충돌합니다.
# 이를 차단하기 위해 해당 모듈을 더미로 등록합니다.
import sys
import types

for mod_name in [
    "launch_testing",
    "launch_testing.tools",
    "launch_testing_ros",
    "launch_testing_ros_pytest_entrypoint",
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

import pytest
from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ledger.models import Transaction

User = get_user_model()


@pytest.fixture
def user(db):
    """테스트용 유저 생성.

    db fixture를 매개변수로 받으면 pytest-django가
    이 테스트에서 DB 접근을 허용해줍니다.
    """
    return User.objects.create_user(
        username="testuser",
        password="testpass123!",
    )


@pytest.fixture
def other_user(db):
    """다른 사용자 — 데이터 격리 테스트용."""
    return User.objects.create_user(
        username="otheruser",
        password="otherpass123!",
    )


@pytest.fixture
def api_client(user):
    """JWT 인증이 적용된 APIClient.

    이 fixture를 사용하면 모든 요청에 자동으로
    Authorization: Bearer <token> 헤더가 붙습니다.
    """
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def unauthenticated_client():
    """인증 없는 APIClient — 401 테스트용."""
    return APIClient()


@pytest.fixture
def sample_transaction(user):
    """테스트용 거래 1건 생성."""
    return Transaction.objects.create(
        user_id=str(user.id),
        occurred_date=date(2026, 2, 13),
        type="expense",
        amount=8000,
        currency="KRW",
        category="식비",
        subcategory="식사",
        merchant="김치찌개집",
        memo="점심",
        source_text="점심 김치찌개 8000원",
    )


@pytest.fixture
def multiple_transactions(user):
    """여러 건의 거래 생성 — 조회/요약 테스트용."""
    txs = [
        Transaction(
            user_id=str(user.id),
            occurred_date=date(2026, 2, 10),
            type="expense",
            amount=5000,
            category="식비",
            subcategory="카페",
        ),
        Transaction(
            user_id=str(user.id),
            occurred_date=date(2026, 2, 11),
            type="expense",
            amount=15000,
            category="교통",
            subcategory="택시",
        ),
        Transaction(
            user_id=str(user.id),
            occurred_date=date(2026, 2, 12),
            type="expense",
            amount=30000,
            category="쇼핑",
            subcategory="생필품",
        ),
        Transaction(
            user_id=str(user.id),
            occurred_date=date(2026, 2, 13),
            type="income",
            amount=100000,
            category="급여",
            subcategory="월급",
        ),
    ]
    return Transaction.objects.bulk_create(txs)
