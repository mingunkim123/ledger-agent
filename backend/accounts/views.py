"""accounts 앱 Views — 회원가입"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import RegisterSerializer


class RegisterView(APIView):
    """POST /accounts/register/ — 회원가입 (인증 불필요)"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"username": user.username, "message": "회원가입이 완료되었습니다."},
            status=status.HTTP_201_CREATED,
        )
