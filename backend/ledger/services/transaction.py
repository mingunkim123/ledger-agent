"""TransactionService — 거래 생성/조회/취소/요약 비즈니스 로직 통합"""

import calendar
import uuid
from datetime import date

from django.db.models import Sum

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


class TransactionService:
    """
    거래 관련 비즈니스 로직 통합.

    ChatView와 TransactionListCreateView에서 중복되던 로직을
    단일 서비스 계층으로 통합하여 DRY 원칙을 준수합니다.
    """

    @staticmethod
    def create_transaction(
        user_id: str,
        args: dict,
        idem_key: str | None = None,
    ) -> dict:
        """
        거래 생성 파이프라인:
        1. 멱등성(idempotency) 캐시 확인
        2. 날짜/금액/카테고리 정규화
        3. 유효성 검증
        4. Transaction 레코드 생성
        5. 멱등성 키 저장
        6. 감사로그 기록
        7. undo 토큰 발급

        Returns:
            dict with tx_id, undo_token, cached 등
        Raises:
            ValueError: 금액/날짜 입력 형식 오류
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

        # ── 4) Transaction 레코드 생성 ──
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

        # ── 5) 멱등성 키 저장 ──
        if idem_key:
            save_idempotency(user_id, idem_key, tx.tx_id)

        # ── 6) 감사로그 ──
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
        log_audit(user_id, "create", tx_id=tx.tx_id, after_snapshot=after_snapshot)

        # ── 7) undo 토큰 ──
        undo_token = str(uuid.uuid4())
        save_undo_token(undo_token, tx.tx_id)

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
    def list_transactions(
        user_id: str,
        from_date=None,
        to_date=None,
        category: str | None = None,
    ):
        """
        거래 목록 조회 (필터링 적용).
        Returns: QuerySet[Transaction]
        """
        qs = Transaction.objects.filter(user_id=user_id)
        if from_date:
            qs = qs.filter(occurred_date__gte=from_date)
        if to_date:
            qs = qs.filter(occurred_date__lte=to_date)
        if category:
            qs = qs.filter(category=category)
        return qs.order_by("-occurred_date", "-created_at")

    @staticmethod
    def undo_transaction(undo_token: str) -> dict:
        """
        거래 취소 파이프라인:
        1. Redis에서 undo_token → tx_id 조회
        2. Transaction 조회
        3. 감사로그 기록
        4. Transaction 삭제
        5. Redis 토큰 삭제

        Returns:
            dict with success, tx_id, message
        Raises:
            UndoTokenExpiredError, TransactionNotFoundError
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

        # ── 3) 감사로그 ──
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

        # ── 4) 삭제 ──
        tx.delete()

        # ── 5) Redis 토큰 삭제 ──
        delete_undo_token(undo_token)

        return {
            "success": True,
            "tx_id": str(tx_id),
            "message": "저장이 취소되었습니다.",
        }

    @staticmethod
    def get_summary(user_id: str, month: str) -> dict:
        """
        월별 카테고리별 지출 합계.

        Args:
            user_id: 사용자 ID
            month: "YYYY-MM" 형식

        Returns:
            dict with month, total, by_category
        """
        year, m = int(month[:4]), int(month[5:7])
        from_date = date(year, m, 1)
        last_day = calendar.monthrange(year, m)[1]
        to_date = date(year, m, last_day)

        qs = (
            Transaction.objects.filter(
                user_id=user_id,
                type="expense",
                occurred_date__gte=from_date,
                occurred_date__lte=to_date,
            )
            .values("category")
            .annotate(cat_total=Sum("amount"))
            .order_by("-cat_total")
        )

        by_category = {row["category"]: row["cat_total"] for row in qs}
        total = sum(by_category.values())

        return {"month": month, "total": total, "by_category": by_category}
