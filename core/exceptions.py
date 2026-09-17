from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as default_exception_handler


class DomainError(Exception):
    """Base class for business-rule violations."""


class InsufficientBalanceError(DomainError):
    pass


class PipelineStateError(DomainError):
    pass


class LegalReserveViolationError(DomainError):
    pass


def drf_exception_handler(exc, context):
    """
    Normalise Django ValidationError and our DomainError into DRF responses.
    """
    from core.exceptions import DomainError

    response = default_exception_handler(exc, context)

    if response is None and isinstance(exc, DjangoValidationError):
        return Response(
            {"detail": exc.messages if hasattr(exc, "messages") else str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if response is None and isinstance(exc, DomainError):
        return Response(
            {"detail": str(exc), "code": exc.__class__.__name__},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return response
