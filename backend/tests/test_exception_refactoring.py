import pytest
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.response import Response
from ledger.exceptions import TransactionValueError, TransactionNotFoundError
from rest_framework.permissions import AllowAny
from django.urls import path


# 테스트용 View 정의
class ExceptionTestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error_type = request.query_params.get("type")
        if error_type == "value_error":
            raise TransactionValueError(detail="Invalid amount")
        elif error_type == "not_found":
            raise TransactionNotFoundError(detail="Transaction not found")
        return Response({"success": True})


urlpatterns = [
    path("test/exception/", ExceptionTestView.as_view(), name="test-exception"),
]


@pytest.mark.urls(__name__)
def test_transaction_value_error_format(client):
    response = client.get("/test/exception/?type=value_error")
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "TRANSACTION_VALUE_ERROR"
    assert data["message"] == "Invalid amount"


@pytest.mark.urls(__name__)
def test_transaction_not_found_error_format(client):
    response = client.get("/test/exception/?type=not_found")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "TRANSACTION_NOT_FOUND"
    assert data["message"] == "Transaction not found"
