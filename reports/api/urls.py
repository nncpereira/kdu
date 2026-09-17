from django.urls import path
from reports.api.views import (
    TrialBalanceView,
    IncomeStatementView,
    BalanceSheetView,
    SurplusDistributionView,
)

app_name = "reports"

urlpatterns = [
    path("trial-balance/", TrialBalanceView.as_view(), name="trial-balance"),
    path("income-statement/", IncomeStatementView.as_view(), name="income-statement"),
    path("balance-sheet/", BalanceSheetView.as_view(), name="balance-sheet"),
    path(
        "surplus-distribution/<uuid:fy_id>/",
        SurplusDistributionView.as_view(),
        name="surplus-distribution",
    ),
]
