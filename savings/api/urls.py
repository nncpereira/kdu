from django.urls import path
from savings.api.views import (
    DepositView,
    WithdrawView,
    TransactionListView,
    MemberVoluntaryView,
)

app_name = "savings"

urlpatterns = [
    path("deposit/", DepositView.as_view(), name="deposit"),
    path("withdraw/", WithdrawView.as_view(), name="withdraw"),
    path("transactions/", TransactionListView.as_view(), name="transactions"),
    path(
        "members/<uuid:member_id>/voluntary/",
        MemberVoluntaryView.as_view(),
        name="member-voluntary",
    ),
]
