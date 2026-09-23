from django.core.exceptions import ValidationError
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
    ShuMemberPayoutSerializer,
)
from shu.models import ShuCalculation, ShuFiscalYear
from shu.services.calculation import create_fiscal_year, run_shu_calculation
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
        calc = get_object_or_404(ShuCalculation, pk=calc_id)
        payouts = calc.payouts.select_related("member")
        return Response(ShuMemberPayoutSerializer(payouts, many=True).data)


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
