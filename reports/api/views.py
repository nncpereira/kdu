from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsBoardOrChecker

from rest_framework.permissions import IsAuthenticated
from reports.services import (
    trial_balance,
    income_statement,
    balance_sheet,
    surplus_distribution,
    dashboard_summary,
)

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reports.pdf import (
    build_trial_balance_pdf,
    build_income_statement_pdf,
    build_balance_sheet_pdf,
    build_surplus_distribution_pdf,
)


def _pdf_response(pdf_bytes: bytes, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


class TrialBalancePdfView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        as_of = request.query_params.get("as_of")
        if not as_of:
            return Response({"detail": "as_of is required."}, status=400)
        pdf = build_trial_balance_pdf(as_of)
        return _pdf_response(pdf, f"trial-balance-{as_of}.pdf")


class IncomeStatementPdfView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if not (start and end):
            return Response({"detail": "start and end are required."}, status=400)
        pdf = build_income_statement_pdf(start, end)
        return _pdf_response(pdf, f"income-statement-{start}-{end}.pdf")


class BalanceSheetPdfView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        as_of = request.query_params.get("as_of")
        if not as_of:
            return Response({"detail": "as_of is required."}, status=400)
        pdf = build_balance_sheet_pdf(as_of)
        return _pdf_response(pdf, f"balance-sheet-{as_of}.pdf")


class SurplusDistributionPdfView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, fy_id):
        pdf = build_surplus_distribution_pdf(fy_id)
        return _pdf_response(pdf, f"shu-{fy_id}.pdf")


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


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dashboard_summary())
