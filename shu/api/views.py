from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsSuperadmin, IsBoardOrChecker
from shu.models import ShuCalculation, ShuFiscalYear
from shu.services.calculation import run_shu_calculation
from shu.services.snapshot import take_monthly_snapshot, aggregate_annual_weighting
from .serializers import ShuCalculationSerializer, ShuMemberPayoutSerializer


class ShuCalculateView(APIView):
    permission_classes = [IsMaker]

    def post(self, request):
        calc = run_shu_calculation(
            fy_id=request.data["fy_id"],
            maker_user=request.user.profile,
        )
        return Response(
            ShuCalculationSerializer(calc).data, status=status.HTTP_201_CREATED
        )


class ShuCalculationDetailView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, calc_id):
        calc = ShuCalculation.objects.get(pk=calc_id)
        return Response(ShuCalculationSerializer(calc).data)


class ShuPayoutListView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, calc_id):
        calc = ShuCalculation.objects.get(pk=calc_id)
        payouts = calc.payouts.select_related("member")
        return Response(ShuMemberPayoutSerializer(payouts, many=True).data)


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
