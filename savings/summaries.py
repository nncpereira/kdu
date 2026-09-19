from pipeline.summaries import register_summary


@register_summary("DEPOSIT")
def _deposit(txn_id):
    from savings.models import Transaction

    t = Transaction.objects.select_related("member").get(id=txn_id)
    return {
        "label": (
            f"{t.member.full_name} — Deposit ${t.requested_amount} "
            f"(oblig ${t.obligatory_portion}, vol ${t.voluntary_portion})"
        ),
        "kind": "DEPOSIT",
        "member_number": t.member.membership_number,
        "member_name": t.member.full_name,
        "amount": str(t.requested_amount),
        "obligatory_portion": str(t.obligatory_portion),
        "voluntary_portion": str(t.voluntary_portion),
    }


@register_summary("WITHDRAWAL")
def _withdrawal(txn_id):
    from savings.models import Transaction

    t = Transaction.objects.select_related("member").get(id=txn_id)
    return {
        "label": f"{t.member.full_name} — Withdraw ${t.requested_amount}",
        "kind": "WITHDRAWAL",
        "member_number": t.member.membership_number,
        "member_name": t.member.full_name,
        "amount": str(t.requested_amount),
    }
