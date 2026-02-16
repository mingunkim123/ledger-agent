"""TransactionService — 거래 생성/조회/취소/요약 비즈니스 로직 통합"""

import calendar
import uuid
from datetime import date

from django.db import transaction
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
                # Redis 작업은 DB 트랜잭션과 무관하지만, 에러 발생 시 DB 롤백을 유도하기 위해 블록 내에 배치
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

            # 5) Redis 토큰 삭제 (DB 롤백 시 이 부분도 실행 취소되는 것은 아니지만, 마지막 단계라 안전)
            delete_undo_token(undo_token)

        return {
            "success": True,
            "tx_id": str(tx_id),
            "message": "저장이 취소되었습니다.",
        }

    @staticmethod
    def get_summary(
        user_id: str,
        month: str | None = None,
        from_date=None,
        to_date=None,
    ) -> dict:
        """
        기간별 카테고리별 지출 합계.

        Args:
            user_id: 사용자 ID
            month: "YYYY-MM" 형식 (옵션)
            from_date: 시작일 (옵션, date 객체)
            to_date: 종료일 (옵션, date 객체)

        month 또는 from_date/to_date 쌍 중 하나가 필요합니다.
        from_date/to_date가 있으면 month보다 우선합니다.

        Returns:
            dict with label, total, by_category
        """
        if from_date and to_date:
            label = f"{from_date} ~ {to_date}"
        elif month:
            year, m = int(month[:4]), int(month[5:7])
            from_date = date(year, m, 1)
            last_day = calendar.monthrange(year, m)[1]
            to_date = date(year, m, last_day)
            label = month
        else:
            raise ValueError("month 또는 from_date/to_date 필수")

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

        return {"label": label, "total": total, "by_category": by_category}

    @staticmethod
    def delete_transaction_by_query(
        user_id: str,
        occurred_date: date | None,
        amount: int,
        category: str | None = None,
        merchant: str | None = None,
    ) -> dict:
        """
        조건에 맞는 가장 최근 거래 삭제 (자연어 삭제용).
        1. 날짜, 금액 필수
        2. 카테고리/가맹점은 선택 (없으면 금액/날짜만으로 검색)
        3. 여러 개면 가장 최근 생성된 것 삭제
        """
        qs = Transaction.objects.filter(
            user_id=user_id,
            amount=amount,
        )
        if occurred_date:
            qs = qs.filter(occurred_date=occurred_date)

        # 카테고리나 가맹점이 있으면 필터 추가
        if category and category != "기타":
            qs = qs.filter(category=category)
        if merchant:
            qs = qs.filter(merchant__icontains=merchant)

        # 가장 최근 것 1개 조회
        target = qs.order_by("-created_at").first()
        if not target:
            return {
                "success": False,
                "message": "일치하는 거래 내역을 찾을 수 없습니다.",
            }

        # 삭제 프로세스 (audit logging 포함) - Atomic
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
    def search_transactions(
        user_id: str,
        keyword: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        category: str | None = None,
    ) -> list[dict]:
        """
        LLM용 거래 검색.
        Returns:
            list[dict]: 검색된 거래 내역 (최대 20개)
        """
        qs = Transaction.objects.filter(user_id=user_id)

        if start_date:
            qs = qs.filter(occurred_date__gte=start_date)
        if end_date:
            qs = qs.filter(occurred_date__lte=end_date)
        if min_amount is not None:
            qs = qs.filter(amount__gte=min_amount)
        if max_amount is not None:
            qs = qs.filter(amount__lte=max_amount)
        if category and category != "기타":
            qs = qs.filter(category=category)

        if keyword:
            # merchant, category, subcategory, memo, source_text 에서 검색
            from django.db.models import Q

            qs = qs.filter(
                Q(merchant__icontains=keyword)
                | Q(category__icontains=keyword)
                | Q(subcategory__icontains=keyword)
                | Q(memo__icontains=keyword)
                | Q(source_text__icontains=keyword)
            )

        # 최신순, 최대 10개만 반환 (LLM 컨텍스트 절약)
        results = []
        for tx in qs.order_by("-occurred_date", "-created_at")[:10]:
            results.append(
                {
                    "tx_id": str(tx.tx_id),
                    "date": str(tx.occurred_date),
                    "amount": tx.amount,
                    "category": tx.category,
                    "merchant": tx.merchant or "",
                    "memo": tx.memo or "",
                }
            )
        return results

    @staticmethod
    def delete_transactions_by_ids(user_id: str, tx_ids: list[str]) -> dict:
        """
        ID 목록으로 거래 일괄 삭제.
        """
        targets = Transaction.objects.filter(user_id=user_id, tx_id__in=tx_ids)
        if not targets.exists():
            return {"success": False, "message": "삭제할 내역을 찾지 못했어요."}

        count = 0
        deleted_details = []

        with transaction.atomic():
            for target in targets:
                # Audit Log
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
