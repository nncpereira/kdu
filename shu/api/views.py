from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import (
    IsMaker,
    IsStaffReadShu,
    IsSuperadmin,
)
from pipeline.services import reject
from shu.api.serializers import (
    CreateFiscalYearSerializer,
    ShuCalculationSerializer,
    ShuFiscalYearSerializer,
    ShuMemberPayoutDetailSerializer,
    ShuMemberPayoutSerializer,
)
from shu.models import (
    ShuCalculation,
    ShuFiscalYear,
    ShuMemberMonthlyBalance,
    ShuMemberPayout,
    ShuWeightingBase,
)
from shu.services.calculation import (
    create_fiscal_year,
    refresh_fiscal_year_totals,
    run_shu_calculation,
)
from shu.services.eligibility import eligible_months, month_weight
from shu.services.snapshot import (
    aggregate_annual_weighting,
    backfill_snapshots,
    take_monthly_snapshot,
)


class FyIdRequestSerializer(serializers.Serializer):
    fy_id = serializers.UUIDField()


class CalcIdRequestSerializer(serializers.Serializer):
    calc_id = serializers.UUIDField()


class ShuFiscalYearListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperadmin()]
        return [IsStaffReadShu()]

    @extend_schema(
        responses={200: ShuFiscalYearSerializer(many=True)},
        tags=["shu"],
        summary="List fiscal years",
    )
    def get(self, request):
        qs = ShuFiscalYear.objects.all().order_by("-year_start")
        return Response(ShuFiscalYearSerializer(qs, many=True).data)

    @extend_schema(
        request=CreateFiscalYearSerializer,
        responses={201: ShuFiscalYearSerializer},
        tags=["shu"],
        summary="Create a fiscal year",
    )
    def post(self, request):
        serializer = CreateFiscalYearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fy = create_fiscal_year(
            serializer.validated_data["year_start"],
            serializer.validated_data["year_end"],
        )
        return Response(
            ShuFiscalYearSerializer(fy).data, status=status.HTTP_201_CREATED
        )


class ShuFiscalYearDetailView(APIView):
    permission_classes = [IsStaffReadShu]

    @extend_schema(
        responses={200: ShuFiscalYearSerializer},
        tags=["shu"],
        summary="Get fiscal year details",
    )
    def get(self, request, pk):
        fy = get_object_or_404(ShuFiscalYear, pk=pk)
        return Response(ShuFiscalYearSerializer(fy).data)


class ShuFiscalYearRefreshView(APIView):
    """Re-read a fiscal year's totals from the ledger (see refresh_fiscal_year_totals)."""

    permission_classes = [IsSuperadmin]

    @extend_schema(
        request=None,
        responses={200: ShuFiscalYearSerializer},
        tags=["shu"],
        summary="Recalculate a fiscal year's totals from the current ledger",
    )
    def post(self, request, pk):
        fy = get_object_or_404(ShuFiscalYear, pk=pk)
        try:
            fy = refresh_fiscal_year_totals(fy)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ShuFiscalYearSerializer(fy).data)


class ShuBackfillView(APIView):
    permission_classes = [IsSuperadmin]

    @extend_schema(
        request=FyIdRequestSerializer,
        responses={200: OpenApiResponse(description="Rows created.")},
        tags=["shu"],
        summary="Backfill monthly snapshots for a fiscal year",
    )
    def post(self, request):
        serializer = FyIdRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fy = get_object_or_404(ShuFiscalYear, pk=serializer.validated_data["fy_id"])
        count = backfill_snapshots(fy)
        return Response({"rows_created": count})


# ====================================================================
# Calculation
# ====================================================================
class ShuCalculateView(APIView):
    permission_classes = [IsMaker]

    @extend_schema(
        request=FyIdRequestSerializer,
        responses={201: ShuCalculationSerializer},
        tags=["shu"],
        summary="Run the SHU calculation for a fiscal year",
    )
    def post(self, request):
        serializer = FyIdRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        calc = run_shu_calculation(
            fy_id=serializer.validated_data["fy_id"],
            maker_user=request.user.profile,
        )
        return Response(
            ShuCalculationSerializer(calc).data, status=status.HTTP_201_CREATED
        )


class ShuFiscalYearCalculationView(APIView):
    permission_classes = [IsStaffReadShu]

    @extend_schema(
        responses={
            200: ShuCalculationSerializer,
            204: OpenApiResponse(
                description="No calculation exists for this fiscal year."
            ),
        },
        tags=["shu"],
        summary="Get the current calculation for a fiscal year",
    )
    def get(self, request, fy_id):
        calc = (
            ShuCalculation.objects.filter(fy_id=fy_id)
            .exclude(status=ShuCalculation.Status.REJECTED)
            .order_by("-created_at")
            .first()
        )
        if not calc:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(ShuCalculationSerializer(calc).data)


class ShuCalculationDetailView(APIView):
    permission_classes = [IsStaffReadShu]

    @extend_schema(
        responses={200: ShuCalculationSerializer},
        tags=["shu"],
        summary="Get calculation details",
    )
    def get(self, request, calc_id):
        calc = get_object_or_404(ShuCalculation, pk=calc_id)
        return Response(ShuCalculationSerializer(calc).data)


class ShuCalculationCancelView(APIView):
    """Cancel a pending SHU calculation created by the current maker."""

    permission_classes = [IsMaker]

    @extend_schema(
        request=None,
        responses={200: ShuCalculationSerializer},
        tags=["shu"],
        summary="Cancel a pending SHU calculation created by the current maker",
    )
    def post(self, request, calc_id):
        calc = get_object_or_404(
            ShuCalculation.objects.select_related("pipeline_actor", "pipeline_actor__maker"),
            pk=calc_id,
        )
        profile = request.user.profile
        if profile.role != "SUPERADMIN" and calc.pipeline_actor.maker_id != profile.id:
            return Response(
                {"detail": "Only the calculation maker or a superadmin can cancel it."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            reject(
                calc.pipeline_actor,
                profile,
                request.data.get("reason", "Cancelled by maker"),
            )
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        calc.refresh_from_db()
        return Response(ShuCalculationSerializer(calc).data)


class ShuPayoutListView(APIView):
    permission_classes = [IsStaffReadShu]

    @extend_schema(
        responses={200: ShuMemberPayoutSerializer(many=True)},
        tags=["shu"],
        summary="List member payouts for a calculation",
    )
    def get(self, request, calc_id):
        from members.models import Member

        calc = get_object_or_404(ShuCalculation, pk=calc_id)
        payouts = calc.payouts.select_related("member")
        data = list(ShuMemberPayoutSerializer(payouts, many=True).data)

        # Active/Dormant members without a payout row weren't eligible for
        # this FY (e.g. joined after the 15th of its only remaining month)
        # rather than forgotten — surface them explicitly instead of just
        # omitting them from the list.
        paid_member_ids = {p.member_id for p in payouts}
        ineligible = Member.objects.filter(
            status__in=["Active", "Dormant"]
        ).exclude(id__in=paid_member_ids)
        for m in ineligible:
            data.append(
                {
                    "id": None,
                    "member": str(m.id),
                    "member_number": m.membership_number,
                    "full_name": m.full_name,
                    "jasa_simpanan_gross": "0.00",
                    "jasa_bunga_gross": "0.00",
                    "net_payout": "0.00",
                    "status": "NOT_ELIGIBLE",
                }
            )
        return Response(data)


class ShuPayoutDetailView(APIView):
    """
    Everything behind one member's payout, for manual verification: their
    monthly balances (with the weight applied to each), weighted savings
    units, loan interest paid, and the pool totals used in the
    proportional split.
    """

    permission_classes = [IsStaffReadShu]

    @extend_schema(
        responses={200: ShuMemberPayoutDetailSerializer},
        tags=["shu"],
        summary="Get the weighting breakdown behind a member's SHU payout",
    )
    def get(self, request, calc_id, member_id):
        calc = get_object_or_404(ShuCalculation, pk=calc_id)
        payout = get_object_or_404(
            ShuMemberPayout.objects.select_related("member"),
            calc=calc,
            member_id=member_id,
        )
        weighting = get_object_or_404(
            ShuWeightingBase, fy=calc.fy, member_id=member_id
        )

        totals = ShuWeightingBase.objects.filter(fy=calc.fy).aggregate(
            units=models.Sum("weighted_savings_units"),
            interest=models.Sum("loan_interest_paid"),
        )

        eligible = eligible_months(
            payout.member.date_joined, calc.fy.year_start, calc.fy.year_end
        )

        monthly = []
        for snap in ShuMemberMonthlyBalance.objects.filter(
            fy=calc.fy, member_id=member_id
        ).order_by("month_date"):
            is_eligible = snap.month_date in eligible
            weight = month_weight(snap.month_date.month) if is_eligible else 0
            monthly.append(
                {
                    "month_date": snap.month_date,
                    "total_balance": snap.total_balance,
                    "weight": weight,
                    "weighted_balance": snap.total_balance * weight,
                    "eligible": is_eligible,
                }
            )

        data = {
            "member_number": payout.member.membership_number,
            "full_name": payout.member.full_name,
            "months_active": weighting.months_active,
            "sum_weighted_balance": weighting.sum_weighted_balance,
            "weighted_savings_units": weighting.weighted_savings_units,
            "loan_interest_paid": weighting.loan_interest_paid,
            "monthly_balances": monthly,
            "total_weighted_savings_units": totals["units"] or 0,
            "total_loan_interest_paid": totals["interest"] or 0,
            "jasa_simpanan_pool": calc.jasa_simpanan_amt,
            "jasa_bunga_pool": calc.jasa_bunga_amt,
            "jasa_simpanan_gross": payout.jasa_simpanan_gross,
            "jasa_bunga_gross": payout.jasa_bunga_gross,
            "net_payout": payout.net_payout,
        }
        return Response(ShuMemberPayoutDetailSerializer(data).data)


# ====================================================================
# Superadmin triggers
# ====================================================================
class ShuSnapshotTriggerView(APIView):
    permission_classes = [IsSuperadmin]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(description="Rows created.")},
        tags=["shu"],
        summary="Trigger a monthly snapshot now",
    )
    def post(self, request):
        count = take_monthly_snapshot()
        return Response({"rows_created": count})


class ShuAggregationTriggerView(APIView):
    permission_classes = [IsSuperadmin]

    @extend_schema(
        request=FyIdRequestSerializer,
        responses={200: OpenApiResponse(description="Rows created.")},
        tags=["shu"],
        summary="Aggregate annual weighting for a fiscal year",
    )
    def post(self, request):
        serializer = FyIdRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fy = get_object_or_404(ShuFiscalYear, pk=serializer.validated_data["fy_id"])
        count = aggregate_annual_weighting(fy)
        return Response({"rows_created": count})
