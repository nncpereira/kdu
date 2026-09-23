from django.urls import path

from pipeline.api.views import (
    CertifyActorView,
    CheckActorView,
    PendingCertifyListView,
    PendingCheckListView,
    RejectActorView,
)

app_name = "pipeline"

urlpatterns = [
    path("pending-check/", PendingCheckListView.as_view(), name="pending-check"),
    path("pending-certify/", PendingCertifyListView.as_view(), name="pending-certify"),
    path("<uuid:pk>/check/", CheckActorView.as_view(), name="check"),
    path("<uuid:pk>/certify/", CertifyActorView.as_view(), name="certify"),
    path("<uuid:pk>/reject/", RejectActorView.as_view(), name="reject"),
]
