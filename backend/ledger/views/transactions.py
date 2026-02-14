"""POST/GET /transactions — 거래 CRUD (Thin View)"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ledger.serializers import (
    CreateTransactionSerializer,
    TransactionListQuerySerializer,
    TransactionResponseSerializer,
)
from ledger.services.transaction import TransactionService


class TransactionListCreateView(APIView):
    """POST /transactions/ — 거래 생성, GET /transactions/ — 거래 조회"""

    def post(self, request):
        """거래 생성"""
        serializer = CreateTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = str(request.user.id)  # ← JWT 토큰에서 추출

        try:
            result = TransactionService.create_transaction(
                user_id=user_id,
                args=data,
                idem_key=data.get("idem_key"),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if result.get("cached"):
            return Response(
                {"tx_id": result["tx_id"], "cached": True, "undo_token": None}
            )

        return Response(
            {
                "tx_id": result["tx_id"],
                "cached": False,
                "undo_token": result["undo_token"],
            }
        )

    def get(self, request):
        """거래 조회"""
        query_serializer = TransactionListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        user_id = str(request.user.id)  # ← JWT 토큰에서 추출

        transactions = TransactionService.list_transactions(
            user_id=user_id,
            from_date=params.get("from_date"),
            to_date=params.get("to_date"),
            category=params.get("category"),
        )

        response_serializer = TransactionResponseSerializer(transactions, many=True)
        return Response({"transactions": response_serializer.data})
