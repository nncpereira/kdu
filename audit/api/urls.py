from django.urls import path

from audit.api.views import (
    AuditLogDetailView,
    AuditLogExportView,
    AuditLogListView,
    LedgerActivityListView,
    NotificationsView,
)

app_name = "audit"

urlpatterns = [
    path("log/", AuditLogListView.as_view(), name="log-list"),
    path("log/export/", AuditLogExportView.as_view(), name="log-export"),
    path("log/<uuid:pk>/", AuditLogDetailView.as_view(), name="log-detail"),
    path("ledger/", LedgerActivityListView.as_view(), name="ledger-list"),
    path("notifications/", NotificationsView.as_view(), name="notifications"),
]
