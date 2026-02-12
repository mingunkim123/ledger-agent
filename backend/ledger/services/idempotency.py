"""Idempotency 서비스 - Django ORM 사용"""

from uuid import UUID

from ledger.models import IdempotencyKey


def get_cached_tx_id(user_id: str, idem_key: str) -> UUID | None:
    """idempotency_keys에서 캐시된 tx_id 조회."""
    try:
        entry = IdempotencyKey.objects.get(user_id=user_id, idem_key=idem_key)
        return entry.tx_id
    except IdempotencyKey.DoesNotExist:
        return None


def save_idempotency(user_id: str, idem_key: str, tx_id: UUID) -> None:
    """idempotency_keys에 (user_id, idem_key, tx_id) 저장."""
    IdempotencyKey.objects.create(
        user_id=user_id,
        idem_key=idem_key,
        tx_id=tx_id,
    )
