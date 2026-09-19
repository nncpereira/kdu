"""
Resolvers that turn a pipeline actor's target_record_id into a human-readable
summary for the Checker/Certifier UI.

Apps register their resolvers at startup via the @register_summary decorator.
"""

from typing import Callable, Optional

_RESOLVERS: dict[str, Callable] = {}


def register_summary(transaction_type: str):
    def decorator(func: Callable):
        _RESOLVERS[transaction_type] = func
        return func

    return decorator


def get_summary(transaction_type: str, target_record_id) -> Optional[dict]:
    resolver = _RESOLVERS.get(transaction_type)
    if resolver is None:
        return None
    try:
        return resolver(target_record_id)
    except Exception:
        return None
