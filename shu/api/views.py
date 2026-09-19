from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ValidationError

from core.permissions import (
    IsMaker,
    IsSuperadmin,
    IsBoardOrChecker,
    IsStaffReadShu,
)
from shu.api.serializers import (
    ShuCalculationSerializer,
    ShuMemberPayoutSerializer,
    ShuFiscalYearSerializer,
    CreateFiscalYearSerializer,
)
from shu.models import ShuCalculation, ShuFiscalYear
from shu.services.calculation import run_shu_calculation, create_fiscal_year
from pipeline.services import reject
from shu.services.snapshot import (
    take_monthly_snapshot,
    aggregate_annual_weighting,
    backfill_snapshots,
)


class ShuFiscalYearListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperadmin()]
        return [IsStaffReadShu()]  # ← was IsBoardOrChecker

    def get(self, request):
        qs = ShuFiscalYear.objects.all().order_by("-year_start")
        return Response(ShuFiscalYearSerializer(qs, many=True).data)

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
    permission_classes = [IsStaffReadShu]  # ← was IsBoardOrChecker

    def get(self, request, pk):
        fy = ShuFiscalYear.objects.get(pk=pk)
        return Response(ShuFiscalYearSerializer(fy).data)


class ShuBackfillView(APIView):
    permission_classes = [IsSuperadmin]

    def post(self, request):
        fy_id = request.data.get("fy_id")
        if not fy_id:
            return Response(
                {"detail": "fy_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        fy = ShuFiscalYear.objects.get(pk=fy_id)
        count = backfill_snapshots(fy)
        return Response({"rows_created": count})


# ====================================================================
# Calculation
# ====================================================================
class ShuCalculateView(APIView):
    permission_classes = [IsMaker]  # now includes SUPERADMIN

    def post(self, request):
        calc = run_shu_calculation(
            fy_id=request.data["fy_id"],
            maker_user=request.user.profile,
        )
        return Response(
            ShuCalculationSerializer(calc).data, status=status.HTTP_201_CREATED
        )


class ShuFiscalYearCalculationView(APIView):
    permission_classes = [IsStaffReadShu]

    def get(self, request, fy_id):
        calc = (
            ShuCalculation.objects.filter(fy_id=fy_id)
            .exclude(status=ShuCalculation.Status.REJECTED)
            .order_by("-created_at")
            .first()
        )
        if calc is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(ShuCalculationSerializer(calc).data)


class ShuCalculationDetailView(APIView):
    permission_classes = [IsStaffReadShu]  # ← was IsBoardOrChecker

    def get(self, request, calc_id):
        calc = ShuCalculation.objects.get(pk=calc_id)
        return Response(ShuCalculationSerializer(calc).data)


class ShuCalculationCancelView(APIView):
    """Cancel a pending SHU calculation created by the current maker."""

    permission_classes = [IsMaker]

    def post(self, request, calc_id):
        calc = ShuCalculation.objects.select_related("pipeline_actor", "pipeline_actor__maker").get(pk=calc_id)
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
    permission_classes = [IsStaffReadShu]  # ← was IsBoardOrChecker

    def get(self, request, calc_id):
        calc = ShuCalculation.objects.get(pk=calc_id)
        payouts = calc.payouts.select_related("member")
        return Response(ShuMemberPayoutSerializer(payouts, many=True).data)


# ====================================================================
# Superadmin triggers
# ====================================================================
class ShuSnapshotTriggerView(APIView):
    permission_classes = [IsSuperadmin]

    def post(self, request):
        count = take_monthly_snapshot()
        return Response({"rows_created": count})


class ShuAggregationTriggerView(APIView):
    permission_classes = [IsSuperadmin]

    def post(self, request):
        fy = ShuFiscalYear.objects.get(pk=request.data["fy_id"])
        count = aggregate_annual_weighting(fy)
        return Response({"rows_created": count})
