from pipeline.summaries import register_summary


@register_summary("JOURNAL_REVERSAL")
def _reversal(req_id):
    from ledger.models import ReversalRequest

    req = ReversalRequest.objects.select_related("original_journal_entry").get(
        id=req_id
    )
    return {
        "label": f"Reverse: {req.original_journal_entry.description}",
        "kind": "JOURNAL_REVERSAL",
        "original_description": req.original_journal_entry.description,
        "original_amount": None,
        "reason": req.reason,
    }
