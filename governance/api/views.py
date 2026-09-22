from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMaker, IsCertifier, IsBoardOrChecker
from governance.models import GlobalConfig, GlobalConfigChange
from governance.services import propose_change, certify_change
from .serializers import (
    GlobalConfigSerializer,
    GlobalConfigChangeSerializer,
    ProposeChangeSerializer,
)


class ProposeConfigChangeView(APIView):
    permission_classes = [IsMaker]

    def post(self, request):
        serializer = ProposeChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change = propose_change(
            maker_user=request.user.profile,
            request=request,
            **serializer.validated_data,
        )
        return Response(
            GlobalConfigChangeSerializer(change).data,
            status=status.HTTP_201_CREATED,
        )


class CertifyConfigChangeView(APIView):
    permission_classes = [IsCertifier]

    def post(self, request, pk):
        change = GlobalConfigChange.objects.get(pk=pk)
        change = certify_change(
            change,
            certifier_user=request.user.profile,
            request=request,
        )
        return Response(GlobalConfigChangeSerializer(change).data)


class GlobalConfigListView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        qs = GlobalConfig.objects.filter(status="ACTIVE").order_by("parameter_key")
        return Response(GlobalConfigSerializer(qs, many=True).data)


class GlobalConfigChangeListView(APIView):
    permission_classes = [IsBoardOrChecker]

    def get(self, request):
        qs = GlobalConfigChange.objects.order_by("-created_at")[:100]
        return Response(GlobalConfigChangeSerializer(qs, many=True).data)
