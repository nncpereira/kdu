from django.urls import path
from members.api.views import (
    MemberListCreateView,
    MemberDetailView,
    PayInitialCapitalView,
    MemberExitView,
)

from members.api.me_views import (
    MyProfileView,
    MySavingsView,
    MyTransactionsView,
    MyLoansView,
    MyShuStatementView,
)

app_name = "members"

urlpatterns = [
    path("", MemberListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", MemberDetailView.as_view(), name="detail"),
    path(
        "<uuid:pk>/initial-capital/",
        PayInitialCapitalView.as_view(),
        name="initial-capital",
    ),
    path("<uuid:pk>/exit/", MemberExitView.as_view(), name="exit"),
    path("me/", MyProfileView.as_view(), name="me"),
    path("me/savings/", MySavingsView.as_view(), name="me-savings"),
    path("me/transactions/", MyTransactionsView.as_view(), name="me-transactions"),
    path("me/loans/", MyLoansView.as_view(), name="me-loans"),
    path("me/shu/<int:year>/", MyShuStatementView.as_view(), name="me-shu"),
]
