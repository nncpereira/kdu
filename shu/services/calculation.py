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


def _compute_fy_totals(year_start, year_end) -> dict:
    """
    Totals from the immutable ledger, as of `year_end`:
      - net_surplus              = revenue − expenses for the period
      - kapital_sosial           = net balance of 3101
      - accumulated_reserva_legal = net balance of 3501
    """
    from ledger.services import account_net_balance
    from reports.services import income_statement

    inc = income_statement(year_start, year_end)
    return {
        "net_surplus": inc["net_surplus"],
        "kapital_sosial": account_net_balance("3101", as_of=year_end),
        "accumulated_reserva_legal": account_net_balance("3501", as_of=year_end),
    }


@transaction.atomic
def create_fiscal_year(year_start, year_end) -> ShuFiscalYear:
    """Create a new OPEN fiscal year, computing its totals from the ledger."""
    if year_end <= year_start:
        raise ValidationError("year_end must be after year_start.")

    if ShuFiscalYear.objects.filter(year_start=year_start, year_end=year_end).exists():
        raise ValidationError("A fiscal year with the same dates already exists.")

    totals = _compute_fy_totals(year_start, year_end)
    return ShuFiscalYear.objects.create(
        year_start=year_start,
        year_end=year_end,
        status=ShuFiscalYear.Status.OPEN,
        **totals,
    )


@transaction.atomic
def refresh_fiscal_year_totals(fy: ShuFiscalYear) -> ShuFiscalYear:
    """
    Re-read net_surplus/kapital_sosial/accumulated_reserva_legal from the
    ledger. These are captured once at create_fiscal_year() time and don't
    auto-update as later revenue/expense/capital activity is posted, so
    this is the only way to pick up e.g. an expense recorded after the FY
    was created but before its SHU calculation is certified.

    Blocked once a non-rejected calculation exists for this FY — that
    calculation already has split amounts computed against the old
    totals, and refreshing here would leave them silently inconsistent.
    """
    if fy.status != ShuFiscalYear.Status.OPEN:
        raise ValidationError("Only an OPEN fiscal year's totals can be refreshed.")

    if fy.calculations.exclude(status=ShuCalculation.Status.REJECTED).exists():
        raise ValidationError(
            "Cancel (reject) the existing SHU calculation for this fiscal "
            "year before refreshing its totals."
        )

    totals = _compute_fy_totals(fy.year_start, fy.year_end)
    for field, value in totals.items():
        setattr(fy, field, value)
    fy.save(update_fields=[*totals.keys(), "updated_at"])
    return fy
