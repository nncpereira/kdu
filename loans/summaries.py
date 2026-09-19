from pipeline.summaries import register_summary


@register_summary("LOAN_DISBURSE")
def _loan_disburse(loan_id):
    from loans.models import Loan

    loan = Loan.objects.select_related("member").get(id=loan_id)
    return {
        "label": (
            f"{loan.member.full_name} — Disburse ${loan.principal_original} "
            f"@ {loan.monthly_rate}/mo × {loan.term_months}"
        ),
        "kind": "LOAN_DISBURSE",
        "member_number": loan.member.membership_number,
        "member_name": loan.member.full_name,
        "amount": str(loan.principal_original),
        "monthly_rate": str(loan.monthly_rate),
        "term_months": loan.term_months,
    }


@register_summary("LOAN_REPAY")
def _loan_repay(repayment_id):
    from loans.models import LoanRepayment

    r = LoanRepayment.objects.select_related("loan__member").get(id=repayment_id)
    m = r.loan.member
    total = r.principal_paid + r.interest_paid
    return {
        "label": (
            f"{m.full_name} — Repayment principal ${r.principal_paid}, "
            f"interest ${r.interest_paid}"
        ),
        "kind": "LOAN_REPAY",
        "member_number": m.membership_number,
        "member_name": m.full_name,
        "amount": str(total),
        "principal_paid": str(r.principal_paid),
        "interest_paid": str(r.interest_paid),
        "mode": r.mode,
    }
