from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import (
    IsBoardOrChecker,
    IsCertifier,
    IsCertifierOrSuperadmin,
    IsChecker,
)
from pipeline.api.serializers import PipelineActorSerializer
from pipeline.models import TransactionPipelineActor
from pipeline.services import certify, check, reject


class RejectRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class PendingCheckListView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: PipelineActorSerializer(many=True)},
        tags=["pipeline"],
        summary="Transactions awaiting the Checker",
    )
    def get(self, request):
        qs = TransactionPipelineActor.objects.filter(
            status=TransactionPipelineActor.Status.PENDING_CHECK
        ).order_by("-updated_at")
        return Response(PipelineActorSerializer(qs, many=True).data)


class PendingCertifyListView(APIView):
    permission_classes = [IsCertifierOrSuperadmin]

    @extend_schema(
        responses={200: PipelineActorSerializer(many=True)},
        tags=["pipeline"],
        summary="Transactions awaiting the Certifier",
    )
    def get(self, request):
        qs = TransactionPipelineActor.objects.filter(
            status=TransactionPipelineActor.Status.PENDING_CERTIFY
        ).order_by("-updated_at")
        return Response(PipelineActorSerializer(qs, many=True).data)


class CheckActorView(APIView):
    permission_classes = [IsChecker]

    @extend_schema(
        request=None,
        responses={200: PipelineActorSerializer},
        tags=["pipeline"],
        summary="Check a pending transaction",
    )
    def post(self, request, pk):
        # actor = TransactionPipelineActor.objects.get(pk=pk)
        actor = get_object_or_404(TransactionPipelineActor, pk=pk)
        check(actor, checker_user=request.user.profile)
        return Response(PipelineActorSerializer(actor).data)


class CertifyActorView(APIView):
    permission_classes = [IsCertifier]

    @extend_schema(
        request=None,
        responses={200: PipelineActorSerializer},
        tags=["pipeline"],
        summary="Certify a pending transaction",
    )
    def post(self, request, pk):
        # actor = TransactionPipelineActor.objects.get(pk=pk)
        actor = get_object_or_404(TransactionPipelineActor, pk=pk)
        certify(actor, certifier_user=request.user.profile)
        return Response(PipelineActorSerializer(actor).data)


class RejectActorView(APIView):
    permission_classes = [IsChecker]  # or IsCertifier depending on stage

    @extend_schema(
        request=RejectRequestSerializer,
        responses={200: PipelineActorSerializer},
        tags=["pipeline"],
        summary="Reject a pending transaction",
    )
    def post(self, request, pk):
        # actor = TransactionPipelineActor.objects.get(pk=pk)
        actor = get_object_or_404(TransactionPipelineActor, pk=pk)
        reason = request.data.get("reason", "")
        reject(actor, rejector_user=request.user.profile, reason=reason)
        return Response(PipelineActorSerializer(actor).data)
