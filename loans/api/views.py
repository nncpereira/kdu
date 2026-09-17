from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsBoardOrChecker
from loans.api.serializers import (
    LoanSerializer,
    LoanOriginateSerializer,
    ManualRepaymentSerializer,
    ScheduledRepaymentSerializer,
    LoanRepaymentSerializer,
)
from loans.models import Loan, LoanRepayment
from loans.services import originate_loan, repay_manual, repay_scheduled
from members.models import Member


class LoanListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMaker()]
        return [IsBoardOrChecker()]

    def get(self, request):
        qs = Loan.objects.select_related("member").order_by("-created_at")
        member_id = request.query_params.get("member")
        if member_id:
            qs = qs.filter(member_id=member_id)
        return Response(LoanSerializer(qs[:200], many=True).data)

    def post(self, request):
        serializer = LoanOriginateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = get_object_or_404(Member, pk=serializer.validated_data.pop("member"))
        loan = originate_loan(
            member=member,
            maker_user=request.user.profile,
            **serializer.validated_data,
        )
        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)


class LoanDetailView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        return Response(LoanSerializer(loan).data)


class ManualRepaymentView(APIView):
    permission_classes = [IsMaker]

    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        serializer = ManualRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repayment = repay_manual(
            loan=loan,
            maker_user=request.user.profile,
            **serializer.validated_data,
        )
        return Response(
            LoanRepaymentSerializer(repayment).data, status=status.HTTP_201_CREATED
        )


class ScheduledRepaymentView(APIView):
    permission_classes = [IsMaker]

    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        serializer = ScheduledRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repayment = repay_scheduled(
            loan=loan,
            maker_user=request.user.profile,
            **serializer.validated_data,
        )
        return Response(
            LoanRepaymentSerializer(repayment).data, status=status.HTTP_201_CREATED
        )


class RepaymentListView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, pk):
        qs = LoanRepayment.objects.filter(loan_id=pk).order_by("-payment_date")
        return Response(LoanRepaymentSerializer(qs, many=True).data)
