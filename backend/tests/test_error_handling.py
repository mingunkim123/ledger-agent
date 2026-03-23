import pytest
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.response import Response
from core.exceptions import ApplicationError
from rest_framework.permissions import AllowAny
from django.urls import path
from rest_framework.exceptions import NotFound


# 테스트용 View 정의
class ErrorTestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error_type = request.query_params.get("type")
        if error_type == "application":
            raise ApplicationError(
                detail="Custom application error", code="CUSTOM_ERROR"
            )
        elif error_type == "not_found":
            raise NotFound("Resource not found")
        elif error_type == "value_error":
            raise ValueError("This is a simplified value error")
        elif error_type == "zero_division":
            1 / 0
        return Response({"success": True})


urlpatterns = [
    path("test/error/", ErrorTestView.as_view(), name="test-error"),
]


@pytest.mark.urls(__name__)
def test_application_error_format(client):
    response = client.get("/test/error/?type=application")
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "CUSTOM_ERROR"
    assert data["message"] == "Custom application error"
    assert data["data"] is None


@pytest.mark.urls(__name__)
def test_drf_exception_handling(client):
    # DRF 내부에서 발생하는 NotFound 예외 테스트
    response = client.get("/test/error/?type=not_found")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "NOT_FOUND"
    assert "Resource not found" in data["message"]
