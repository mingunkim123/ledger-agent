"""GET /summary — 월별 지출 요약 (Thin View)"""

from rest_framework.response import Response
from rest_framework.views import APIView

from ledger.serializers import SummaryQuerySerializer
from ledger.services.transaction import TransactionService


class SummaryView(APIView):
    """GET /summary/ — 월별 카테고리별 지출 합계"""

    def get(self, request):
        query_serializer = SummaryQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        user_id = str(request.user.id)  # ← JWT 토큰에서 추출

        result = TransactionService.get_summary(
            user_id=user_id,
            month=params["month"],
        )

        return Response(result)
