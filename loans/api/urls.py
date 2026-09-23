from django.urls import path

from loans.api.views import (
    LoanDetailView,
    LoanListCreateView,
    ManualRepaymentView,
    RepaymentListView,
    ScheduledRepaymentView,
)

app_name = "loans"

urlpatterns = [
    path("", LoanListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", LoanDetailView.as_view(), name="detail"),
    path("<uuid:pk>/repay/manual/", ManualRepaymentView.as_view(), name="repay-manual"),
    path(
        "<uuid:pk>/repay/scheduled/",
        ScheduledRepaymentView.as_view(),
        name="repay-scheduled",
    ),
    path("<uuid:pk>/repayments/", RepaymentListView.as_view(), name="repayments"),
]
