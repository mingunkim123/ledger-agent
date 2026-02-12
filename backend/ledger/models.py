"""Django ORM 모델 - 기존 DB 테이블 매핑"""

import uuid

from django.db import models


class Transaction(models.Model):
    """거래 내역 (기존 transactions 테이블)"""

    TYPE_CHOICES = [
        ("expense", "지출"),
        ("income", "수입"),
    ]

    tx_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.TextField()
    occurred_date = models.DateField()
    type = models.TextField(choices=TYPE_CHOICES)
    amount = models.IntegerField()
    currency = models.TextField(default="KRW")
    category = models.TextField()
    subcategory = models.TextField(default="기타")
    merchant = models.TextField(null=True, blank=True)
    memo = models.TextField(null=True, blank=True)
    source_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-occurred_date", "-created_at"]
        indexes = [
            models.Index(fields=["user_id", "-occurred_date"], name="idx_tx_user_date"),
            models.Index(fields=["user_id", "category"], name="idx_tx_user_cat"),
            models.Index(fields=["user_id", "subcategory"], name="idx_tx_user_subcat"),
        ]

    def __str__(self):
        return f"[{self.occurred_date}] {self.category} {self.amount:,}원"


class IdempotencyKey(models.Model):
    """중복 방지 키 (기존 idempotency_keys 테이블)"""

    user_id = models.TextField()
    idem_key = models.TextField()
    tx = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        db_column="tx_id",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idempotency_keys"
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "idem_key"], name="pk_idempotency"
            ),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.idem_key}"


class AuditLog(models.Model):
    """감사 로그 (기존 audit_logs 테이블)"""

    ACTION_CHOICES = [
        ("create", "생성"),
        ("update", "수정"),
        ("delete", "삭제"),
        ("undo", "취소"),
    ]

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.TextField()
    action = models.TextField(choices=ACTION_CHOICES)
    tx = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="tx_id",
    )
    before_snapshot = models.JSONField(null=True, blank=True)
    after_snapshot = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user_id", "-created_at"], name="idx_audit_user_created"
            ),
        ]

    def __str__(self):
        return f"[{self.action}] {self.user_id} @ {self.created_at}"
