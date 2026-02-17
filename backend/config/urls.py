"""루트 URL 라우팅 — API 버저닝 포함"""

from django.contrib import admin
from django.urls import include, path

from ledger.views import HealthDBView, HealthView, RootView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # 루트
    path("admin/", admin.site.urls),
    path("", RootView.as_view()),
    # API v1
    path("api/v1/", include("ledger.urls")),
    path("api/v1/accounts/", include("accounts.urls")),
    # API v2 (현재는 v1과 동일하게 연결 - 추후 분리 가능)
    path("api/v2/", include("ledger.urls", namespace="v2")),
    # OpenAPI Schema & UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # 헬스체크 (버저닝 없이 직접 접근 가능)
    path("health/", HealthView.as_view()),
    path("health/db/", HealthDBView.as_view()),
]
