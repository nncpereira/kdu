from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsStaffReadLedger
from ledger.api.serializers import (
    CreateReversalSerializer,
    ReversalRequestSerializer,
)
from ledger.models import JournalEntry, ReversalRequest
from pipeline.services import create_pipeline


class ReversalListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMaker()]
        return [IsStaffReadLedger()]

    @extend_schema(
        responses={200: ReversalRequestSerializer(many=True)},
        tags=["ledger"],
        summary="List journal entry reversal requests",
    )
    def get(self, request):
        qs = ReversalRequest.objects.select_related(
            "original_journal_entry", "pipeline_actor__maker__user"
        ).order_by("-created_at")[:200]
        return Response(ReversalRequestSerializer(qs, many=True).data)

    @extend_schema(
        request=CreateReversalSerializer,
        responses={201: ReversalRequestSerializer},
        tags=["ledger"],
        summary="Request a reversal of a certified journal entry",
    )
    def post(self, request):
        serializer = CreateReversalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        original = get_object_or_404(
            JournalEntry,
            pk=serializer.validated_data["original_journal_entry"],
        )

        if original.status != JournalEntry.Status.CERTIFIED:
            return Response(
                {"detail": "Only certified journal entries can be reversed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if original.reversals.exists():
            return Response(
                {"detail": "This entry has already been reversed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            req = ReversalRequest.objects.create(
                original_journal_entry=original,
                source_type=serializer.validated_data["source_type"],
                source_id=serializer.validated_data.get("source_id"),
                reason=serializer.validated_data["reason"],
                status=ReversalRequest.Status.PENDING_CHECK,
            )

            actor = create_pipeline(
                transaction_type="JOURNAL_REVERSAL",
                target_record_id=req.id,
                maker_user=request.user.profile,
            )
            req.pipeline_actor = actor
            req.save(update_fields=["pipeline_actor"])

        return Response(
            ReversalRequestSerializer(req).data,
            status=status.HTTP_201_CREATED,
        )


class ReversalDetailView(APIView):
    permission_classes = [IsStaffReadLedger]

    @extend_schema(
        responses={200: ReversalRequestSerializer},
        tags=["ledger"],
        summary="Get a reversal request",
    )
    def get(self, request, pk):
        req = get_object_or_404(ReversalRequest, pk=pk)
        return Response(ReversalRequestSerializer(req).data)
