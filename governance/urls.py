from django.urls import path
from governance.api.views import ProposeConfigChangeView, CertifyConfigChangeView

urlpatterns = [
    path("propose/", ProposeConfigChangeView.as_view(), name="config-propose"),
    path(
        "certify/<uuid:pk>/", CertifyConfigChangeView.as_view(), name="config-certify"
    ),
]
