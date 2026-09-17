from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsBoardOrChecker
from members.models import Member
from savings.api.serializers import (
    TransactionSerializer,
    DepositRequestSerializer,
    WithdrawRequestSerializer,
    VoluntaryDepositSerializer,
)
from savings.models import Transaction, MemberVoluntaryDeposit
from savings.services import deposit, withdraw


class DepositView(APIView):
    permission_classes = [IsMaker]

    def post(self, request):
        serializer = DepositRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = get_object_or_404(Member, pk=serializer.validated_data["member"])
        txn = deposit(
            member=member,
            amount=serializer.validated_data["amount"],
            maker_user=request.user.profile,
        )
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class WithdrawView(APIView):
    permission_classes = [IsMaker]

    def post(self, request):
        serializer = WithdrawRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = get_object_or_404(Member, pk=serializer.validated_data["member"])
        txn = withdraw(
            member=member,
            amount=serializer.validated_data["amount"],
            maker_user=request.user.profile,
        )
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class TransactionListView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        qs = Transaction.objects.select_related("member").order_by("-created_at")
        member_id = request.query_params.get("member")
        if member_id:
            qs = qs.filter(member_id=member_id)
        txn_type = request.query_params.get("type")
        if txn_type:
            qs = qs.filter(transaction_type=txn_type)
        return Response(TransactionSerializer(qs[:200], many=True).data)


class MemberVoluntaryView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request, member_id):
        vd = get_object_or_404(MemberVoluntaryDeposit, member_id=member_id)
        return Response(VoluntaryDepositSerializer(vd).data)
