from pipeline.summaries import register_summary


@register_summary("MEMBER_ONBOARD")
def _member_onboard(onboarding_id):
    from members.models import MemberOnboarding

    ob = MemberOnboarding.objects.select_related("member").get(id=onboarding_id)
    m = ob.member
    return {
        "label": f"{m.full_name} — Initial capital ${ob.initial_capital_amount}",
        "kind": "INITIAL_CAPITAL",
        "member_number": m.membership_number,
        "member_name": m.full_name,
        "amount": str(ob.initial_capital_amount),
    }


@register_summary("MEMBER_EXIT")
def _member_exit(exit_id):
    from members.models import MemberExitRequest

    req = MemberExitRequest.objects.select_related("member").get(id=exit_id)
    m = req.member
    return {
        "label": f"{m.full_name} — Exit / refund ${req.refund_amount}",
        "kind": "EXIT",
        "member_number": m.membership_number,
        "member_name": m.full_name,
        "amount": str(req.refund_amount),
    }
