from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsStaffReadExpenses
from expenses.api.serializers import ExpenseCreateSerializer, ExpenseSerializer
from expenses.models import Expense
from expenses.services import record_expense


class ExpenseListCreateView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMaker()]
        return [IsStaffReadExpenses()]

    @extend_schema(
        responses={200: ExpenseSerializer(many=True)},
        tags=["expenses"],
        summary="List expenses",
    )
    def get(self, request):
        qs = Expense.objects.all().order_by("-payment_date")
        account_code = request.query_params.get("expense_account_code")
        if account_code:
            qs = qs.filter(expense_account_code=account_code)
        return Response(
            ExpenseSerializer(qs[:200], many=True, context={"request": request}).data
        )

    @extend_schema(
        request=ExpenseCreateSerializer,
        responses={201: ExpenseSerializer},
        tags=["expenses"],
        summary="Record an expense",
    )
    def post(self, request):
        serializer = ExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expense = record_expense(
            description=serializer.validated_data["description"],
            amount=serializer.validated_data["amount"],
            expense_account_code=serializer.validated_data["expense_account_code"],
            payment_date=serializer.validated_data.get("payment_date"),
            receipt=serializer.validated_data.get("receipt"),
            maker_user=request.user.profile,
        )
        return Response(
            ExpenseSerializer(expense, context={"request": request}).data,
            status=201,
        )


class ExpenseDetailView(APIView):
    permission_classes = [IsStaffReadExpenses]

    @extend_schema(
        responses={200: ExpenseSerializer},
        tags=["expenses"],
        summary="Get an expense",
    )
    def get(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        return Response(ExpenseSerializer(expense, context={"request": request}).data)
