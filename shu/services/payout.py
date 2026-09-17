from django.core.exceptions import ValidationError
from django.db import transaction

from ledger.services import post_journal_entry
from shu.models import ShuCalculation, ShuMemberPayout

RETAINED_SURPLUS = "3900"
RESERVA_LEGAL = "3501"
ADMIN_FUND = "3502"
SHU_PAYABLE = "3200"
CASH = "1001"


@transaction.atomic
def post_reserve_allocation(calc: ShuCalculation, certifier_user) -> None:
    """
    Dr 3900 Retained Surplus
    Cr 3501 Reserva Legal
    Cr 3502 Admin & Operational Fund
    """
    if calc.reserve_journal_entry_id:
        return  # idempotent

    lines = [(RETAINED_SURPLUS, "DEBIT", calc.reserva_legal_amt + calc.admin_fund_amt)]
    if calc.reserva_legal_amt > 0:
        lines.append((RESERVA_LEGAL, "CREDIT", calc.reserva_legal_amt))
    if calc.admin_fund_amt > 0:
        lines.append((ADMIN_FUND, "CREDIT", calc.admin_fund_amt))

    je = post_journal_entry(
        description=f"SHU reserves – FY {calc.fy.year_start}–{calc.fy.year_end}",
        lines=lines,
        created_by=certifier_user,
        entry_date=calc.fy.year_end,
        auto_certify=True,
        certified_by=certifier_user,
    )
    calc.reserve_journal_entry = je
    calc.save(update_fields=["reserve_journal_entry"])


@transaction.atomic
def post_member_payouts(calc: ShuCalculation, certifier_user) -> int:
    """
    For each member payout, post a JE:
        Dr 3200 SHU Payable
        Cr 1001 Cash
    Marks payout rows PAID and calc PAYOUT_COMPLETE.
    """
    if calc.status == ShuCalculation.Status.PAYOUT_COMPLETE:
        return 0

    count = 0
    for payout in calc.payouts.filter(
        status=ShuMemberPayout.Status.DRAFT
    ).select_related("member"):
        je = post_journal_entry(
            description=f"SHU payout – {payout.member.membership_number}",
            lines=[
                (SHU_PAYABLE, "DEBIT", payout.net_payout),
                (CASH, "CREDIT", payout.net_payout),
            ],
            created_by=certifier_user,
            entry_date=calc.fy.year_end,
            auto_certify=True,
            certified_by=certifier_user,
        )
        payout.journal_entry = je
        payout.status = ShuMemberPayout.Status.PAID
        payout.save(update_fields=["journal_entry", "status", "updated_at"])
        count += 1
    return count


@transaction.atomic
def finalise_payout(calc: ShuCalculation, certifier_user) -> ShuCalculation:
    """
    Full payout: reserve allocation + member payouts + status transition.
    """
    if calc.status != ShuCalculation.Status.CERTIFIED:
        raise ValidationError("Calculation must be CERTIFIED before payout.")

    post_reserve_allocation(calc, certifier_user)
    post_member_payouts(calc, certifier_user)

    calc.status = ShuCalculation.Status.PAYOUT_COMPLETE
    calc.save(update_fields=["status", "updated_at"])

    # Close the fiscal year
    fy = calc.fy
    fy.status = fy.Status.CLOSED
    fy.save(update_fields=["status", "updated_at"])
    return calc
