from django.urls import path

from reports.api.views import (
    BalanceSheetView,
    IncomeStatementView,
    SurplusDistributionView,
    TrialBalanceView,
)

urlpatterns = [
    path("trial-balance/", TrialBalanceView.as_view(), name="report-trial-balance"),
    path("income-statement/", IncomeStatementView.as_view(), name="report-income"),
    path("balance-sheet/", BalanceSheetView.as_view(), name="report-balance"),
    path(
        "surplus-distribution/<uuid:fy_id>/",
        SurplusDistributionView.as_view(),
        name="report-shu",
    ),
]
