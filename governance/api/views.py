from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsBoardOrChecker, IsCertifier, IsMaker
from governance.models import GlobalConfig, GlobalConfigChange
from governance.services import certify_change, propose_change

from .serializers import (
    GlobalConfigChangeSerializer,
    GlobalConfigSerializer,
    ProposeChangeSerializer,
)


class ProposeConfigChangeView(APIView):
    permission_classes = [IsMaker]

    @extend_schema(
        request=ProposeChangeSerializer,
        responses={201: GlobalConfigChangeSerializer},
        tags=["governance"],
        summary="Propose a governance config change",
    )
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

    @extend_schema(
        request=None,
        responses={200: GlobalConfigChangeSerializer},
        tags=["governance"],
        summary="Certify a pending governance config change",
    )
    def post(self, request, pk):
        # change = GlobalConfigChange.objects.get(pk=pk)
        change = get_object_or_404(GlobalConfigChange, pk=pk)
        change = certify_change(
            change,
            certifier_user=request.user.profile,
            request=request,
        )
        return Response(GlobalConfigChangeSerializer(change).data)


class GlobalConfigListView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: GlobalConfigSerializer(many=True)},
        tags=["governance"],
        summary="List active governance config values",
    )
    def get(self, request):
        qs = GlobalConfig.objects.filter(status="ACTIVE").order_by("parameter_key")
        return Response(GlobalConfigSerializer(qs, many=True).data)


class GlobalConfigChangeListView(APIView):
    permission_classes = [IsBoardOrChecker]

    @extend_schema(
        responses={200: GlobalConfigChangeSerializer(many=True)},
        tags=["governance"],
        summary="List recent governance config change proposals",
    )
    def get(self, request):
        qs = GlobalConfigChange.objects.order_by("-created_at")[:100]
        return Response(GlobalConfigChangeSerializer(qs, many=True).data)
