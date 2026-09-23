"""
URL configuration for kdu_tmp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenVerifyView,
)

from core.views import health_check
from users.api.auth_views import (
    CookieLogoutView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
)

admin.site.site_header = "KDU Cooperative Admin"
admin.site.site_title = "KDU Admin"
admin.site.index_title = "Cooperative Administration"

urlpatterns = [
    # Django admin (with custom SHU calculator page)
    path("admin/", admin.site.urls),
    # Health
    path("health/", health_check, name="health"),
    # JWT auth
    path(
        "api/v1/auth/token/",
        CookieTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/auth/token/refresh/",
        CookieTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("api/v1/auth/logout/", CookieLogoutView.as_view(), name="logout"),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API v1 (one include per app)
    path("api/v1/users/", include(("users.api.urls", "users"), namespace="users")),
    path(
        "api/v1/members/", include(("members.api.urls", "members"), namespace="members")
    ),
    path(
        "api/v1/savings/", include(("savings.api.urls", "savings"), namespace="savings")
    ),
    path("api/v1/loans/", include(("loans.api.urls", "loans"), namespace="loans")),
    path("api/v1/ledger/", include(("ledger.api.urls", "ledger"), namespace="ledger")),
    path(
        "api/v1/expenses/",
        include(("expenses.api.urls", "expenses"), namespace="expenses"),
    ),
    path("api/v1/shu/", include(("shu.api.urls", "shu"), namespace="shu")),
    path(
        "api/v1/governance/",
        include(("governance.api.urls", "governance"), namespace="governance"),
    ),
    path(
        "api/v1/reports/", include(("reports.api.urls", "reports"), namespace="reports")
    ),
    path(
        "api/v1/pipeline/",
        include(("pipeline.api.urls", "pipeline"), namespace="pipeline"),
    ),
    # HTML staff/member login (server-rendered)
    path("auth/", include(("users.urls", "auth"), namespace="auth")),
    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/audit/", include(("audit.api.urls", "audit"), namespace="audit")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
