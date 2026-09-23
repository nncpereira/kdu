from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsStaffReadSavings
from members.models import Member
from savings.api.serializers import (
    DepositRequestSerializer,
    TransactionSerializer,
    VoluntaryDepositSerializer,
    WithdrawRequestSerializer,
)
from savings.models import MemberVoluntaryDeposit, Transaction
from savings.services import deposit, withdraw


class DepositView(APIView):
    permission_classes = [IsMaker]

    @extend_schema(
        request=DepositRequestSerializer,
        responses={201: TransactionSerializer},
        tags=["savings"],
        summary="Record a cash deposit",
    )
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

    @extend_schema(
        request=WithdrawRequestSerializer,
        responses={201: TransactionSerializer},
        tags=["savings"],
        summary="Record a withdrawal from voluntary deposits",
    )
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
    permission_classes = [IsStaffReadSavings]

    @extend_schema(
        responses={200: TransactionSerializer(many=True)},
        tags=["savings"],
        summary="List savings transactions",
    )
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
    permission_classes = [IsStaffReadSavings]

    @extend_schema(
        responses={200: VoluntaryDepositSerializer},
        tags=["savings"],
        summary="Get a member's voluntary deposit balance",
    )
    def get(self, request, member_id):
        member = get_object_or_404(Member, pk=member_id)
        vd = MemberVoluntaryDeposit.objects.filter(member=member).first()

        if vd is None:
            return Response(
                {
                    "member": str(member.id),
                    "balance_available": "0.00",
                    "balance_held_pipeline": "0.00",
                    "updated_at": None,
                }
            )

        return Response(VoluntaryDepositSerializer(vd).data)
