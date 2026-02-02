"""감사로그 서비스 (Step 7-1) - audit_logs 기록"""
import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def log_audit(
    session: AsyncSession,
    user_id: str,
    action: str,
    tx_id: UUID | None = None,
    before_snapshot: dict | None = None,
    after_snapshot: dict | None = None,
) -> None:
    """
    audit_logs에 기록.
    action: create, update, delete, undo
    """
    before_json = json.dumps(before_snapshot, ensure_ascii=False) if before_snapshot else None
    after_json = json.dumps(after_snapshot, ensure_ascii=False) if after_snapshot else None

    await session.execute(
        text("""
            INSERT INTO audit_logs (user_id, action, tx_id, before_snapshot, after_snapshot)
            VALUES (:user_id, :action, :tx_id, CAST(:before_snapshot AS jsonb), CAST(:after_snapshot AS jsonb))
        """),
        {
            "user_id": user_id,
            "action": action,
            "tx_id": str(tx_id) if tx_id else None,
            "before_snapshot": before_json,
            "after_snapshot": after_json,
        },
    )
