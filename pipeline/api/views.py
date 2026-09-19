from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import (
    IsChecker,
    IsCertifier,
    IsCertifierOrSuperadmin,
    IsBoardOrChecker,
)
from pipeline.api.serializers import PipelineActorSerializer
from pipeline.models import TransactionPipelineActor
from pipeline.services import check, certify, reject


class PendingCheckListView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        qs = TransactionPipelineActor.objects.filter(
            status=TransactionPipelineActor.Status.PENDING_CHECK
        ).order_by("-updated_at")
        return Response(PipelineActorSerializer(qs, many=True).data)


class PendingCertifyListView(APIView):
    permission_classes = [IsCertifierOrSuperadmin]

    def get(self, request):
        qs = TransactionPipelineActor.objects.filter(
            status=TransactionPipelineActor.Status.PENDING_CERTIFY
        ).order_by("-updated_at")
        return Response(PipelineActorSerializer(qs, many=True).data)


class CheckActorView(APIView):
    permission_classes = [IsChecker]

    def post(self, request, pk):
        actor = TransactionPipelineActor.objects.get(pk=pk)
        check(actor, checker_user=request.user.profile)
        return Response(PipelineActorSerializer(actor).data)


class CertifyActorView(APIView):
    permission_classes = [IsCertifier]

    def post(self, request, pk):
        actor = TransactionPipelineActor.objects.get(pk=pk)
        certify(actor, certifier_user=request.user.profile)
        return Response(PipelineActorSerializer(actor).data)


class RejectActorView(APIView):
    permission_classes = [IsChecker]  # or IsCertifier depending on stage

    def post(self, request, pk):
        actor = TransactionPipelineActor.objects.get(pk=pk)
        reason = request.data.get("reason", "")
        reject(actor, rejector_user=request.user.profile, reason=reason)
        return Response(PipelineActorSerializer(actor).data)
