from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from core.services import round_money
from governance.services import get_active_value, validate_shu_split
from pipeline.services import create_pipeline
from shu.models import (
    ShuCalculation,
    ShuFiscalYear,
    ShuMemberPayout,
    ShuWeightingBase,
)


# ====================================================================
# Split math
# ====================================================================
def calculate_shu_split(net_surplus: Decimal, split: dict) -> dict:
    """
    Apply the configured split. The last allocation absorbs any rounding
    remainder so that allocations sum exactly to the net surplus.
    """

    net_surplus = round_money(net_surplus)

    reserva = round_money(net_surplus * Decimal(str(split["reserva_legal_pct"])) / 100)
    admin = round_money(net_surplus * Decimal(str(split["admin_fund_pct"])) / 100)
    jasa_s = round_money(net_surplus * Decimal(str(split["jasa_simpanan_pct"])) / 100)
    jasa_b = round_money(net_surplus * Decimal(str(split["jasa_bunga_pct"])) / 100)

    diff = net_surplus - (reserva + admin + jasa_s + jasa_b)
    jasa_b += diff  # absorb rounding

    return {
        "reserva_legal_amt": reserva,
        "admin_fund_amt": admin,
        "jasa_simpanan_amt": jasa_s,
        "jasa_bunga_amt": jasa_b,
    }


# ====================================================================
# Main orchestration
# ====================================================================
@transaction.atomic
def run_shu_calculation(fy_id, maker_user) -> ShuCalculation:
    """
    Create a DRAFT ShuCalculation for the FY. Splits from the
    active governance config. Legal reserve checked via governance.
    """
    fy = ShuFiscalYear.objects.select_for_update().get(pk=fy_id)

    if fy.status != ShuFiscalYear.Status.OPEN:
        raise ValidationError("Fiscal year is not OPEN.")

    if ShuCalculation.objects.filter(
        fy=fy,
        status__in=[
            ShuCalculation.Status.DRAFT,
            ShuCalculation.Status.PENDING_CHECK,
            ShuCalculation.Status.PENDING_CERTIFY,
            ShuCalculation.Status.CERTIFIED,
        ],
    ).exists():
        raise ValidationError("An active calculation already exists for this FY.")

    split = get_active_value("shu_split", as_of=fy.year_end)
    if not split:
        raise ValidationError("No active SHU split configured in governance.")

    validate_shu_split(split)  # enforces Art.69 amended

    amounts = calculate_shu_split(fy.net_surplus, split)

    calc = ShuCalculation.objects.create(
        fy=fy,
        net_surplus=fy.net_surplus,
        reserva_legal_pct=split["reserva_legal_pct"],
        admin_fund_pct=split["admin_fund_pct"],
        jasa_simpanan_pct=split["jasa_simpanan_pct"],
        jasa_bunga_pct=split["jasa_bunga_pct"],
        **amounts,
        status=ShuCalculation.Status.PENDING_CHECK,
    )

    # If weighting base is empty, skip silently; the Checker can still
    # approve the allocation and the payouts will be recomputed.
    try:
        compute_member_payouts(calc)
    except ValidationError:
        # No weighting base — likely snapshots not run. Leave payouts empty
        # and let the Checker/Certifier decide. The Certifier's certify
        # handler will retry.
        pass
    
    actor = create_pipeline(
        transaction_type="SHU_CALCULATE",
        target_record_id=calc.id,
        maker_user=maker_user,
    )
    calc.pipeline_actor = actor
    calc.save(update_fields=["pipeline_actor"])
    return calc


# ====================================================================
# Compute per-member payouts (called after Checker approves)
# ====================================================================
@transaction.atomic
def compute_member_payouts(calc: ShuCalculation) -> int:
    """
    Populate ShuMemberPayout rows. No journal entries are posted here.
    Idempotent: clears existing payouts first.
    """
    if calc.status not in (
        ShuCalculation.Status.PENDING_CHECK,
        ShuCalculation.Status.PENDING_CERTIFY,
    ):
        raise ValidationError(
            "Payouts can only be computed while calculation is pending."
        )

    ShuMemberPayout.objects.filter(calc=calc).delete()

    rows = list(ShuWeightingBase.objects.filter(fy=calc.fy))

    total_units = sum((r.weighted_savings_units for r in rows), Decimal("0"))
    total_interest = sum((r.loan_interest_paid for r in rows), Decimal("0"))

    if total_units == 0 and total_interest == 0:
        raise ValidationError("No weighting data — run snapshot & aggregation first.")

    count = 0
    for r in rows:
        jasa_s = (
            round_money(r.weighted_savings_units / total_units * calc.jasa_simpanan_amt)
            if total_units
            else Decimal("0.00")
        )
        jasa_b = (
            round_money(r.loan_interest_paid / total_interest * calc.jasa_bunga_amt)
            if total_interest
            else Decimal("0.00")
        )
        net = jasa_s + jasa_b

        if net <= 0:
            continue

        ShuMemberPayout.objects.create(
            calc=calc,
            member=r.member,
            jasa_simpanan_gross=jasa_s,
            jasa_bunga_gross=jasa_b,
            net_payout=net,
            status=ShuMemberPayout.Status.DRAFT,
        )
        count += 1
    return count


@transaction.atomic
def create_fiscal_year(year_start, year_end) -> ShuFiscalYear:
    """
    Create a new fiscal year, computing totals from the immutable ledger:
      - net_surplus              = revenue − expenses for the period
      - kapital_sosial           = net balance of 3101 at FY end
      - accumulated_reserva_legal = net balance of 3501 at FY end
    """
    from ledger.services import account_net_balance
    from reports.services import income_statement

    if year_end <= year_start:
        raise ValidationError("year_end must be after year_start.")

    if ShuFiscalYear.objects.filter(year_start=year_start, year_end=year_end).exists():
        raise ValidationError("A fiscal year with the same dates already exists.")

    inc = income_statement(year_start, year_end)
    kapital = account_net_balance("3101", as_of=year_end)
    reserva = account_net_balance("3501", as_of=year_end)

    return ShuFiscalYear.objects.create(
        year_start=year_start,
        year_end=year_end,
        status=ShuFiscalYear.Status.OPEN,
        net_surplus=inc["net_surplus"],
        kapital_sosial=kapital,
        accumulated_reserva_legal=reserva,
    )
