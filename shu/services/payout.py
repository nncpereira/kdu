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
    Dr 3900 Retained Surplus (full net surplus allocated this cycle)
    Cr 3501 Reserva Legal
    Cr 3502 Admin & Operational Fund
    Cr 3200 SHU Payable (Jasa Simpanan + Jasa Bunga owed to members,
             drawn down by post_member_payouts() below as each member is paid)
    """
    if calc.reserve_journal_entry_id:
        return  # idempotent

    member_pool = calc.jasa_simpanan_amt + calc.jasa_bunga_amt
    lines = [(RETAINED_SURPLUS, "DEBIT", calc.total_allocated)]
    if calc.reserva_legal_amt > 0:
        lines.append((RESERVA_LEGAL, "CREDIT", calc.reserva_legal_amt))
    if calc.admin_fund_amt > 0:
        lines.append((ADMIN_FUND, "CREDIT", calc.admin_fund_amt))
    if member_pool > 0:
        lines.append((SHU_PAYABLE, "CREDIT", member_pool))

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

    # Close the fiscal year, re-reading its totals so the reserve
    # allocation just posted above (and anything else recorded since
    # creation) is reflected rather than left at a stale snapshot.
    from shu.services.calculation import _compute_fy_totals

    fy = calc.fy
    totals = _compute_fy_totals(fy.year_start, fy.year_end)
    for field, value in totals.items():
        setattr(fy, field, value)
    fy.status = fy.Status.CLOSED
    fy.save(update_fields=[*totals.keys(), "status", "updated_at"])
    return calc
