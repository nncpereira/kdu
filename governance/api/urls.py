from django.urls import path
from governance.api.views import (
    ProposeConfigChangeView,
    CertifyConfigChangeView,
    GlobalConfigListView,
    GlobalConfigChangeListView,
)

app_name = "governance"

urlpatterns = [
    path("config/", GlobalConfigListView.as_view(), name="config-list"),
    path("config/propose/", ProposeConfigChangeView.as_view(), name="config-propose"),
    path(
        "config/certify/<uuid:pk>/",
        CertifyConfigChangeView.as_view(),
        name="config-certify",
    ),
    path("changes/", GlobalConfigChangeListView.as_view(), name="changes-list"),
]
