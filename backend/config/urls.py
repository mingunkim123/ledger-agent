"""루트 URL 라우팅 — API 버저닝 포함"""

from django.urls import include, path

from ledger.views import HealthDBView, HealthView, RootView

urlpatterns = [
    # 루트
    path("", RootView.as_view()),
    # API v1
    path("api/v1/", include("ledger.urls")),
    # 헬스체크 (버저닝 없이 직접 접근 가능)
    path("health/", HealthView.as_view()),
    path("health/db/", HealthDBView.as_view()),
]
