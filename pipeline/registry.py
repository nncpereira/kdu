"""
Simple registry for pipeline completion handlers.

Domain apps register handlers via decorators:

    from pipeline.registry import register

    @register("DEPOSIT", "on_certify")
    def on_deposit_certified(actor, user):
        ...

Handlers receive (actor, user) for on_check / on_certify, and
(actor, user, reason) for on_reject.
"""

from collections.abc import Callable

_HANDLERS: dict[tuple[str, str], list[Callable]] = {}


def register(transaction_type: str, event: str):
    """
    Decorator. Valid events: "on_check", "on_certify", "on_reject".
    """
    if event not in {"on_check", "on_certify", "on_reject"}:
        raise ValueError(f"Unsupported pipeline event: {event}")

    def decorator(func):
        _HANDLERS.setdefault((transaction_type, event), []).append(func)
        return func

    return decorator


def get_handlers(transaction_type: str, event: str) -> list[Callable]:
    return _HANDLERS.get((transaction_type, event), [])


def clear_handlers():
    """Used by tests to reset state."""
    _HANDLERS.clear()
