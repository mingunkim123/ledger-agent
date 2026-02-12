"""Health 엔드포인트"""

from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView


class RootView(APIView):
    """GET / — 앱 정보"""

    def get(self, request):
        return Response({"app": "가계부 에이전트", "status": "ok"})


class HealthView(APIView):
    """GET /health/ — 기본 헬스체크"""

    def get(self, request):
        return Response({"status": "healthy"})


class HealthDBView(APIView):
    """GET /health/db/ — DB 연결 확인"""

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return Response({"status": "healthy", "database": "connected"})
