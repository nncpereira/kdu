from django.urls import path

from shu.api.views import (
    ShuAggregationTriggerView,
    ShuBackfillView,
    ShuCalculateView,
    ShuCalculationCancelView,
    ShuCalculationDetailView,
    ShuFiscalYearCalculationView,
    ShuFiscalYearDetailView,
    ShuFiscalYearListCreateView,
    ShuFiscalYearRefreshView,
    ShuPayoutDetailView,
    ShuPayoutListView,
    ShuSnapshotTriggerView,
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
    path(
        "fiscal-years/<uuid:pk>/refresh/",
        ShuFiscalYearRefreshView.as_view(),
        name="fy-refresh",
    ),
    # Data preparation
    path("backfill/", ShuBackfillView.as_view(), name="backfill"),
    # Calculation lifecycle
    path("calculate/", ShuCalculateView.as_view(), name="calculate"),
    path("<uuid:calc_id>/", ShuCalculationDetailView.as_view(), name="calc-detail"),
    path(
        "<uuid:calc_id>/cancel/",
        ShuCalculationCancelView.as_view(),
        name="calc-cancel",
    ),
    path(
        "<uuid:calc_id>/payouts/",
        ShuPayoutListView.as_view(),
        name="calc-payouts",
    ),
    path(
        "<uuid:calc_id>/payouts/<uuid:member_id>/detail/",
        ShuPayoutDetailView.as_view(),
        name="calc-payout-detail",
    ),
    # Superadmin triggers
    path("snapshot/", ShuSnapshotTriggerView.as_view(), name="snapshot"),
    path("aggregate/", ShuAggregationTriggerView.as_view(), name="aggregate"),
]
