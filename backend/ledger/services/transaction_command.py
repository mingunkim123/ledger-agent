"""TransactionCommandService — 거래 생성, 취소, 삭제 (Write)"""

import uuid
from datetime import date

from django.db import transaction

from ledger.exceptions import TransactionNotFoundError, UndoTokenExpiredError
from ledger.models import Transaction
from ledger.services.audit import log_audit
from ledger.services.idempotency import get_cached_tx_id, save_idempotency
from ledger.services.normalizer import (
    normalize_amount,
    normalize_date,
    resolve_category_subcategory,
)
from ledger.services.undo import (
    delete_undo_token,
    get_tx_id_from_undo_token,
    save_undo_token,
)


class TransactionCommandService:
    """
    거래 상태 변경(Write)을 담당하는 서비스.
    CQRS 패턴의 Command 역할.
    """

    @staticmethod
    def create_transaction(
        user_id: str,
        args: dict,
        idem_key: str | None = None,
    ) -> dict:
        """
        거래 생성 (Atomic).
        """
        # ── 1) 멱등성 캐시 확인 ──
        if idem_key:
            cached_tx_id = get_cached_tx_id(user_id, idem_key)
            if cached_tx_id:
                return {"tx_id": str(cached_tx_id), "cached": True}

        # ── 2) 정규화 ──
        raw_date = args.get("occurred_date") or ""
        if not raw_date:
            occurred_date = date.today()
        else:
            try:
                occurred_date = normalize_date(raw_date)
            except (ValueError, TypeError):
                occurred_date = date.today()

        amount = normalize_amount(args.get("amount", 0))
        source_text = args.get("source_text")
        merchant = args.get("merchant")
        category, subcategory = resolve_category_subcategory(
            args.get("category"),
            args.get("subcategory"),
            source_text=source_text,
            merchant=merchant,
        )

        # ── 3) 유효성 검증 ──
        if amount <= 0:
            raise ValueError("금액은 0보다 커야 합니다")

        tx_type = args.get("type", "expense")
        if tx_type not in ("expense", "income"):
            tx_type = "expense"
        memo = args.get("memo")

        # ── 4~7) Transaction 생성 및 후처리 (Atomic) ──
        try:
            with transaction.atomic():
                # 4) Transaction 레코드 생성
                tx = Transaction.objects.create(
                    user_id=user_id,
                    occurred_date=occurred_date,
                    type=tx_type,
                    amount=amount,
                    currency=args.get("currency", "KRW"),
                    category=category,
                    subcategory=subcategory,
                    merchant=merchant,
                    memo=memo,
                    source_text=source_text,
                )

                # 5) 멱등성 키 저장
                if idem_key:
                    save_idempotency(user_id, idem_key, tx.tx_id)

                # 6) 감사로그
                after_snapshot = {
                    "tx_id": str(tx.tx_id),
                    "user_id": user_id,
                    "occurred_date": str(occurred_date),
                    "type": tx_type,
                    "amount": amount,
                    "currency": args.get("currency", "KRW"),
                    "category": category,
                    "subcategory": subcategory,
                    "merchant": merchant,
                    "memo": memo,
                    "source_text": source_text,
                }
                log_audit(
                    user_id, "create", tx_id=tx.tx_id, after_snapshot=after_snapshot
                )

                # 7) undo 토큰
                undo_token = str(uuid.uuid4())
                save_undo_token(undo_token, tx.tx_id)
        except Exception as e:
            raise e

        return {
            "tx_id": str(tx.tx_id),
            "cached": False,
            "undo_token": undo_token,
            "occurred_date": str(occurred_date),
            "type": tx_type,
            "amount": amount,
            "category": category,
            "subcategory": subcategory,
        }

    @staticmethod
    def undo_transaction(undo_token: str) -> dict:
        """
        거래 취소 (Atomic).
        """
        # ── 1) Redis 조회 ──
        tx_id = get_tx_id_from_undo_token(undo_token)
        if tx_id is None:
            raise UndoTokenExpiredError()

        # ── 2) Transaction 조회 ──
        try:
            tx = Transaction.objects.get(tx_id=tx_id)
        except Transaction.DoesNotExist:
            delete_undo_token(undo_token)
            raise TransactionNotFoundError()

        # ── 3~5) 감사로그 및 삭제 (Atomic) ──
        with transaction.atomic():
            before_snapshot = {
                "tx_id": str(tx.tx_id),
                "user_id": tx.user_id,
                "occurred_date": str(tx.occurred_date),
                "type": tx.type,
                "amount": tx.amount,
                "currency": tx.currency,
                "category": tx.category,
                "subcategory": tx.subcategory,
                "merchant": tx.merchant,
                "memo": tx.memo,
                "source_text": tx.source_text,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
            }
            log_audit(tx.user_id, "undo", tx_id=tx_id, before_snapshot=before_snapshot)

            # 4) 삭제
            tx.delete()

            # 5) Redis 토큰 삭제
            delete_undo_token(undo_token)

        return {
            "success": True,
            "tx_id": str(tx_id),
            "message": "저장이 취소되었습니다.",
        }

    @staticmethod
    def delete_transaction_by_query(
        user_id: str,
        occurred_date: date | None,
        amount: int,
        category: str | None = None,
        merchant: str | None = None,
    ) -> dict:
        """
        조건부 삭제 (Atomic).
        """
        qs = Transaction.objects.filter(
            user_id=user_id,
            amount=amount,
        )
        if occurred_date:
            qs = qs.filter(occurred_date=occurred_date)

        if category and category != "기타":
            qs = qs.filter(category=category)
        if merchant:
            qs = qs.filter(merchant__icontains=merchant)

        target = qs.order_by("-created_at").first()
        if not target:
            return {
                "success": False,
                "message": "일치하는 거래 내역을 찾을 수 없습니다.",
            }

        with transaction.atomic():
            before_snapshot = {
                "tx_id": str(target.tx_id),
                "user_id": target.user_id,
                "occurred_date": str(target.occurred_date),
                "type": target.type,
                "amount": target.amount,
                "category": target.category,
                "subcategory": target.subcategory,
                "merchant": target.merchant,
            }
            log_audit(
                user_id, "delete", tx_id=target.tx_id, before_snapshot=before_snapshot
            )

            target.delete()

        return {
            "success": True,
            "message": f"{target.occurred_date} {target.category} {target.amount:,}원 내역을 삭제했습니다.",
            "deleted_tx": before_snapshot,
        }

    @staticmethod
    def delete_transactions_by_ids(user_id: str, tx_ids: list[str]) -> dict:
        """
        ID 일괄 삭제 (Atomic).
        """
        targets = Transaction.objects.filter(user_id=user_id, tx_id__in=tx_ids)
        if not targets.exists():
            return {"success": False, "message": "삭제할 내역을 찾지 못했어요."}

        count = 0
        deleted_details = []

        with transaction.atomic():
            for target in targets:
                before_snapshot = {
                    "tx_id": str(target.tx_id),
                    "user_id": target.user_id,
                    "occurred_date": str(target.occurred_date),
                    "type": target.type,
                    "amount": target.amount,
                    "category": target.category,
                    "subcategory": target.subcategory,
                    "merchant": target.merchant,
                }
                log_audit(
                    user_id,
                    "delete",
                    tx_id=target.tx_id,
                    before_snapshot=before_snapshot,
                )
                deleted_details.append(
                    f"{target.occurred_date} {target.merchant or target.category} {target.amount}"
                )
                target.delete()
                count += 1

        return {
            "success": True,
            "message": f"{count}건의 내역을 삭제했습니다.",
            "details": deleted_details,
        }
