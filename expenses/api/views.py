from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from core.permissions import IsMaker, IsStaffReadExpenses
from expenses.api.serializers import ExpenseSerializer, ExpenseCreateSerializer
from expenses.models import Expense
from expenses.services import record_expense


class ExpenseListCreateView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMaker()]
        return [IsStaffReadExpenses()]

    def get(self, request):
        qs = Expense.objects.all().order_by("-payment_date")
        return Response(
            ExpenseSerializer(qs[:200], many=True, context={"request": request}).data
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

    def get(self, request, pk):
        expense = Expense.objects.get(pk=pk)
        return Response(ExpenseSerializer(expense, context={"request": request}).data)
