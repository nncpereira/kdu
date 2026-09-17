"""
Helpers to run a Maker-Checker-Certifier pipeline in tests.
"""

from pipeline.services import check, certify, reject


def run_pipeline(actor, *, checker, certifier):
    """Check then certify a pipeline actor and return it."""
    check(actor, checker)
    certify(actor, certifier)
    return actor


def reject_pipeline(actor, *, rejector, reason="test rejection"):
    reject(actor, rejector, reason=reason)
    return actor


def full_pipeline(record, *, checker, certifier):
    """Given a model with .pipeline_actor, run check + certify."""
    return run_pipeline(record.pipeline_actor, checker=checker, certifier=certifier)
