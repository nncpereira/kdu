from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsBoardOrChecker
from reports.pdf import (
    build_balance_sheet_pdf,
    build_income_statement_pdf,
    build_surplus_distribution_pdf,
    build_trial_balance_pdf,
)
from reports.services import (
    balance_sheet,
    dashboard_summary,
    income_statement,
    surplus_distribution,
    trial_balance,
)
from reports.validators import require_date


def _pdf_response(pdf_bytes: bytes, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


class TrialBalancePdfView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: OpenApiResponse(description="PDF file.")},
        tags=["reports"],
        summary="Trial balance PDF",
    )
    def get(self, request):
        as_of = require_date(request.query_params.get("as_of"), "as_of")
        pdf = build_trial_balance_pdf(as_of)
        return _pdf_response(pdf, f"trial-balance-{as_of}.pdf")


class IncomeStatementPdfView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: OpenApiResponse(description="PDF file.")},
        tags=["reports"],
        summary="Trial balance PDF",
    )
    def get(self, request):
        start = require_date(request.query_params.get("start"), "start")
        end = require_date(request.query_params.get("end"), "end")
        pdf = build_income_statement_pdf(start, end)
        return _pdf_response(pdf, f"income-statement-{start}-{end}.pdf")


class BalanceSheetPdfView(APIView):
    permission_classes = [IsBoardOrChecker]
    @extend_schema(
        responses={200: OpenApiResponse(description="PDF file.")},
        tags=["reports"],
        summary="Balance sheet PDF",
    )
    def get(self, request):
        as_of = require_date(request.query_params.get("as_of"), "as_of")
        pdf = build_balance_sheet_pdf(as_of)
        return _pdf_response(pdf, f"balance-sheet-{as_of}.pdf")


class SurplusDistributionPdfView(APIView):
    permission_classes = [IsBoardOrChecker]
    @extend_schema(
        responses={200: OpenApiResponse(description="PDF file.")},
        tags=["reports"],
        summary="Surplus distribution PDF",
    )
    def get(self, request, fy_id):
        pdf = build_surplus_distribution_pdf(fy_id)
        return _pdf_response(pdf, f"shu-{fy_id}.pdf")


class TrialBalanceView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: OpenApiResponse(description="List of trial balance rows.")},
        tags=["reports"],
        summary="Trial balance as of a date",
    )
    def get(self, request):
        as_of = require_date(request.query_params.get("as_of"), "as_of")
        return Response(trial_balance(as_of))


class IncomeStatementView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: OpenApiResponse(description="Income statement for a period.")},
        tags=["reports"],
        summary="Income statement",
    )
    def get(self, request):
        start = require_date(request.query_params.get("start"), "start")
        end = require_date(request.query_params.get("end"), "end")
        return Response(income_statement(start, end))


class BalanceSheetView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: OpenApiResponse(description="Balance sheet as of a date.")},
        tags=["reports"],
        summary="Balance sheet",
    )
    def get(self, request):
        as_of = require_date(request.query_params.get("as_of"), "as_of")
        return Response(balance_sheet(as_of))


class SurplusDistributionView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: OpenApiResponse(description="SHU distribution amounts.")},
        tags=["reports"],
        summary="Surplus distribution for a fiscal year",
    )
    def get(self, request, fy_id):
        result = surplus_distribution(fy_id)
        if not result:
            return Response({"detail": "No SHU calculation found."}, status=404)
        return Response(result)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiResponse(description="Dashboard aggregate summary.")},
        tags=["reports"],
        summary="Dashboard summary",
    )
    def get(self, request):
        return Response(dashboard_summary())
