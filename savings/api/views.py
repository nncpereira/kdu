import uuid

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination
from core.permissions import IsMaker, IsStaffReadSavings
from loans.models import LoanRepayment
from members.models import Member
from savings.api.serializers import (
    DepositRequestSerializer,
    TransactionSerializer,
    VoluntaryDepositSerializer,
    WithdrawRequestSerializer,
)
from savings.models import MemberVoluntaryDeposit, Transaction
from savings.services import deposit, withdraw


def _filter_by_member(qs: QuerySet, value: str, *, path: str) -> QuerySet:
    """
    Accepts either a member's UUID (pk) or a (partial) membership number
    like "KDU-000007", so a "filter by member" box doesn't force callers
    to know the internal UUID.
    """
    try:
        uuid.UUID(value)
        return qs.filter(**{f"{path}_id": value})
    except ValueError:
        return qs.filter(**{f"{path}__membership_number__icontains": value})


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
        summary=(
            "List savings transactions and loan-repayment savings sweeps, "
            "paginated"
        ),
    )
    def get(self, request):
        member_query = request.query_params.get("member")
        txn_type = request.query_params.get("type")

        txn_qs = Transaction.objects.select_related("member")
        if member_query:
            txn_qs = _filter_by_member(txn_qs, member_query, path="member")
        if txn_type:
            txn_qs = txn_qs.filter(transaction_type=txn_type)

        rows = [
            {
                "id": str(t.id),
                "member": str(t.member_id),
                "member_number": t.member.membership_number,
                "transaction_type": t.transaction_type,
                "requested_amount": str(t.requested_amount),
                "obligatory_portion": str(t.obligatory_portion),
                "voluntary_portion": str(t.voluntary_portion),
                "status": t.status,
                "pipeline_actor": str(t.pipeline_actor_id)
                if t.pipeline_actor_id
                else None,
                "journal_entry": str(t.journal_entry_id)
                if t.journal_entry_id
                else None,
                "created_at": t.created_at,
            }
            for t in txn_qs
        ]

        # Only include loan-repayment sweeps when no type filter is
        # active, or the caller explicitly asked for them -- they're
        # neither a DEPOSIT nor a WITHDRAWAL.
        if not txn_type or txn_type == "LOAN_REPAYMENT_SWEEP":
            sweep_qs = LoanRepayment.objects.select_related(
                "loan__member"
            ).filter(Q(obligatory_portion__gt=0) | Q(voluntary_portion__gt=0))
            if member_query:
                sweep_qs = _filter_by_member(
                    sweep_qs, member_query, path="loan__member"
                )
            rows += [
                {
                    "id": str(r.id),
                    "member": str(r.loan.member_id),
                    "member_number": r.loan.member.membership_number,
                    "transaction_type": "LOAN_REPAYMENT_SWEEP",
                    "requested_amount": str(
                        r.obligatory_portion + r.voluntary_portion
                    ),
                    "obligatory_portion": str(r.obligatory_portion),
                    "voluntary_portion": str(r.voluntary_portion),
                    "status": r.status,
                    "pipeline_actor": str(r.pipeline_actor_id)
                    if r.pipeline_actor_id
                    else None,
                    "journal_entry": str(r.journal_entry_id)
                    if r.journal_entry_id
                    else None,
                    "created_at": r.created_at,
                }
                for r in sweep_qs
            ]

        rows.sort(key=lambda row: row["created_at"], reverse=True)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(page)


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
