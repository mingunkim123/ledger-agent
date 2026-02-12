"""POST /undo — 마지막 저장 취소 (Thin View)"""

from rest_framework.response import Response
from rest_framework.views import APIView

from ledger.serializers import UndoRequestSerializer
from ledger.services.transaction import TransactionService


class UndoView(APIView):
    """POST /undo/ — undo_token으로 거래 취소"""

    def post(self, request):
        serializer = UndoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = TransactionService.undo_transaction(
            undo_token=serializer.validated_data["undo_token"],
        )

        return Response(result)
