from django.urls import path
from shu.api.views import (
    ShuCalculateView,
    ShuPayoutListView,
    ShuCalculationDetailView,
    ShuSnapshotTriggerView,
    ShuAggregationTriggerView,
)

app_name = "shu"

urlpatterns = [
    path("calculate/", ShuCalculateView.as_view(), name="calculate"),
    path("<uuid:calc_id>/", ShuCalculationDetailView.as_view(), name="detail"),
    path("<uuid:calc_id>/payouts/", ShuPayoutListView.as_view(), name="payouts"),
    path("snapshot/", ShuSnapshotTriggerView.as_view(), name="snapshot"),
    path("aggregate/", ShuAggregationTriggerView.as_view(), name="aggregate"),
]
