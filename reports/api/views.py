from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsBoardOrChecker
from reports.services import (
    trial_balance,
    income_statement,
    balance_sheet,
    surplus_distribution,
)


class TrialBalanceView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        as_of = request.query_params["as_of"]
        return Response(trial_balance(as_of))


class IncomeStatementView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        start = request.query_params["start"]
        end = request.query_params["end"]
        return Response(income_statement(start, end))


class BalanceSheetView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        as_of = request.query_params["as_of"]
        return Response(balance_sheet(as_of))


class SurplusDistributionView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, fy_id):
        result = surplus_distribution(fy_id)
        if not result:
            return Response({"detail": "No SHU calculation found."}, status=404)
        return Response(result)
