"""DRF Serializers — 입력 검증 + ModelSerializer 기반 응답 직렬화"""

from rest_framework import serializers

from ledger.models import Transaction


# ──────────────────────────────────────────
# 입력 검증 Serializers
# ──────────────────────────────────────────


class ChatRequestSerializer(serializers.Serializer):
    """POST /chat/ 요청"""

    user_id = serializers.CharField()
    message = serializers.CharField()
    session_id = serializers.CharField(required=False, allow_null=True, default=None)
    idem_key = serializers.CharField(required=False, allow_null=True, default=None)
    llm_provider = serializers.CharField(required=False, allow_null=True, default=None)


class CreateTransactionSerializer(serializers.Serializer):
    """POST /transactions/ 요청 — 다양한 포맷 허용 (정규화는 서비스 계층에서 처리)"""

    user_id = serializers.CharField()
    occurred_date = serializers.CharField()  # "어제", "2026-02-13" 등 → normalizer 처리
    type = serializers.ChoiceField(choices=["expense", "income"])
    amount = serializers.CharField()  # "2.3만", "23000" 등 → normalizer 처리
    category = serializers.CharField()
    subcategory = serializers.CharField(required=False, allow_null=True, default=None)
    currency = serializers.CharField(default="KRW")
    merchant = serializers.CharField(required=False, allow_null=True, default=None)
    memo = serializers.CharField(required=False, allow_null=True, default=None)
    source_text = serializers.CharField(required=False, allow_null=True, default=None)
    idem_key = serializers.CharField(required=False, allow_null=True, default=None)


class UndoRequestSerializer(serializers.Serializer):
    """POST /undo/ 요청"""

    undo_token = serializers.CharField()


# ──────────────────────────────────────────
# 쿼리 파라미터 검증 Serializers
# ──────────────────────────────────────────


class TransactionListQuerySerializer(serializers.Serializer):
    """GET /transactions/ 쿼리 파라미터"""

    user_id = serializers.CharField()
    from_date = serializers.DateField(required=False, source="from", default=None)
    to_date = serializers.DateField(required=False, source="to", default=None)
    category = serializers.CharField(required=False, default=None)

    # source="from"/"to" 로 기존 API 파라미터명 호환
    def to_internal_value(self, data):
        """쿼리 파라미터에서 'from', 'to' 키를 'from_date', 'to_date'로 매핑"""
        ret = {}
        ret["user_id"] = data.get("user_id")
        if not ret["user_id"]:
            raise serializers.ValidationError({"user_id": "user_id는 필수입니다"})
        ret["from_date"] = data.get("from")
        ret["to_date"] = data.get("to")
        ret["category"] = data.get("category")
        return ret


class SummaryQuerySerializer(serializers.Serializer):
    """GET /summary/ 쿼리 파라미터"""

    month = serializers.RegexField(
        regex=r"^\d{4}-\d{2}$",
        error_messages={"invalid": "month는 YYYY-MM 형식이어야 합니다"},
    )
    user_id = serializers.CharField()


# ──────────────────────────────────────────
# 응답 Serializers (ModelSerializer)
# ──────────────────────────────────────────


class TransactionResponseSerializer(serializers.ModelSerializer):
    """거래 내역 응답 — Transaction 모델 기반 자동 직렬화"""

    tx_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "tx_id",
            "user_id",
            "occurred_date",
            "type",
            "amount",
            "currency",
            "category",
            "subcategory",
            "merchant",
            "memo",
            "source_text",
            "created_at",
        ]
        read_only_fields = fields
