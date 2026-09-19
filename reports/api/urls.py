from django.urls import path
from reports.api.views import (
    TrialBalanceView,
    IncomeStatementView,
    BalanceSheetView,
    SurplusDistributionView,
    DashboardView,
    TrialBalancePdfView,
    IncomeStatementPdfView,
    BalanceSheetPdfView,
    SurplusDistributionPdfView,
)

app_name = "reports"

urlpatterns = [
    # JSON
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("trial-balance/", TrialBalanceView.as_view(), name="trial-balance"),
    path("income-statement/", IncomeStatementView.as_view(), name="income-statement"),
    path("balance-sheet/", BalanceSheetView.as_view(), name="balance-sheet"),
    path(
        "surplus-distribution/<uuid:fy_id>/",
        SurplusDistributionView.as_view(),
        name="surplus-distribution",
    ),
    # PDF
    path("trial-balance/pdf/", TrialBalancePdfView.as_view(), name="trial-balance-pdf"),
    path(
        "income-statement/pdf/",
        IncomeStatementPdfView.as_view(),
        name="income-statement-pdf",
    ),
    path("balance-sheet/pdf/", BalanceSheetPdfView.as_view(), name="balance-sheet-pdf"),
    path(
        "surplus-distribution/<uuid:fy_id>/pdf/",
        SurplusDistributionPdfView.as_view(),
        name="surplus-distribution-pdf",
    ),
]
