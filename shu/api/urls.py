from django.urls import path
from shu.api.views import (
    ShuFiscalYearListCreateView,
    ShuFiscalYearDetailView,
    ShuFiscalYearCalculationView,
    ShuBackfillView,
    ShuCalculateView,
    ShuCalculationDetailView,
    ShuPayoutListView,
    ShuSnapshotTriggerView,
    ShuAggregationTriggerView,
)

app_name = "shu"

urlpatterns = [
    # Fiscal year
    path(
        "fiscal-years/",
        ShuFiscalYearListCreateView.as_view(),
        name="fy-list-create",
    ),
    # IMPORTANT: this must come BEFORE the `<uuid:pk>/` detail route
    # so it isn't shadowed by a partial match.
    path(
        "fiscal-years/<uuid:fy_id>/calculation/",
        ShuFiscalYearCalculationView.as_view(),
        name="fy-calculation",
    ),
    path(
        "fiscal-years/<uuid:pk>/",
        ShuFiscalYearDetailView.as_view(),
        name="fy-detail",
    ),
    # Data preparation
    path("backfill/", ShuBackfillView.as_view(), name="backfill"),
    # Calculation lifecycle
    path("calculate/", ShuCalculateView.as_view(), name="calculate"),
    path("<uuid:calc_id>/", ShuCalculationDetailView.as_view(), name="calc-detail"),
    path(
        "<uuid:calc_id>/payouts/",
        ShuPayoutListView.as_view(),
        name="calc-payouts",
    ),
    # Superadmin triggers
    path("snapshot/", ShuSnapshotTriggerView.as_view(), name="snapshot"),
    path("aggregate/", ShuAggregationTriggerView.as_view(), name="aggregate"),
]
