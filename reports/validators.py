"""
Small helpers for parsing query-string date filters in report views.
"""

from datetime import date

from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError


def require_date(value: str | None, field: str) -> date:
    """
    Parse a YYYY-MM-DD string into a date. Raise a 400 with a field-specific
    message if the value is missing or malformed.
    """
    if not value:
        raise ValidationError({field: "This query parameter is required."})
    try:
        parsed = parse_date(value)
    except ValueError:
        parsed = None
    if parsed is None:
        raise ValidationError({field: f"Invalid date '{value}'. Expected YYYY-MM-DD."})
    return parsed


def optional_date(value: str | None, field: str) -> date | None:
    if not value:
        return None
    try:
        parsed = parse_date(value)
    except ValueError:
        parsed = None
    if parsed is None:
        raise ValidationError({field: f"Invalid date '{value}'. Expected YYYY-MM-DD."})
    return parsed
