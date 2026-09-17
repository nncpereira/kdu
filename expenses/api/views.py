from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsBoardOrChecker
from expenses.api.serializers import ExpenseSerializer, ExpenseCreateSerializer
from expenses.models import Expense
from expenses.services import record_expense


class ExpenseListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMaker()]
        return [IsBoardOrChecker()]

    def get(self, request):
        qs = Expense.objects.all().order_by("-payment_date")
        return Response(ExpenseSerializer(qs[:200], many=True).data)

    def post(self, request):
        serializer = ExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = record_expense(
            maker_user=request.user.profile,
            **serializer.validated_data,
        )
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


class ExpenseDetailView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, pk):
        expense = Expense.objects.get(pk=pk)
        return Response(ExpenseSerializer(expense).data)
