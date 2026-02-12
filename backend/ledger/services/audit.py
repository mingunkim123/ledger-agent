"""감사로그 서비스 - Django ORM 사용"""

from uuid import UUID

from ledger.models import AuditLog


def log_audit(
    user_id: str,
    action: str,
    tx_id: UUID | None = None,
    before_snapshot: dict | None = None,
    after_snapshot: dict | None = None,
) -> None:
    """audit_logs에 기록."""
    AuditLog.objects.create(
        user_id=user_id,
        action=action,
        tx_id=tx_id,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
    )
