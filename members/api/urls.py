from django.urls import path
from members.api.views import (
    MemberListCreateView,
    MemberDetailView,
    PayInitialCapitalView,
    MemberExitView,
    CreateMemberLoginView,
    ResetMemberLoginPasswordView
)
from members.api.me_views import (
    MyDashboardView,
    MyProfileView,
    MySavingsView,
    MyTransactionsView,
    MyLoansView,
    MyShuStatementView,
)

app_name = "members"

urlpatterns = [
    # Staff
    path("", MemberListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", MemberDetailView.as_view(), name="detail"),
    path(
        "<uuid:pk>/initial-capital/",
        PayInitialCapitalView.as_view(),
        name="initial-capital",
    ),
    path("<uuid:pk>/exit/", MemberExitView.as_view(), name="exit"),
    # Member self-service
    path("me/dashboard/", MyDashboardView.as_view(), name="me-dashboard"),
    path("me/", MyProfileView.as_view(), name="me-profile"),
    path("me/savings/", MySavingsView.as_view(), name="me-savings"),
    path("me/transactions/", MyTransactionsView.as_view(), name="me-transactions"),
    path("me/loans/", MyLoansView.as_view(), name="me-loans"),
    path("me/shu/", MyShuStatementView.as_view(), name="me-shu-all"),
    path("me/shu/<int:year>/", MyShuStatementView.as_view(), name="me-shu"),
    # Superadmin: member login management
    path(
        "<uuid:pk>/create-login/", CreateMemberLoginView.as_view(), name="create-login"
    ),
    path(
        "<uuid:pk>/reset-login-password/",
        ResetMemberLoginPasswordView.as_view(),
        name="reset-login-password",
    ),
]
