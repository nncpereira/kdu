from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from core.services import round_money, today
from governance.services import get_active_value
from ledger.services import post_journal_entry
from loans.models import Loan, LoanRepayment
from pipeline.services import create_pipeline

CASH = "1001"
LOANS_RECEIVABLE = "1301"
INTEREST_INCOME = "40100"
KAPITAL_SOSIAL = "3101"
VOLUNTARY_DEPOSIT = "2101"


# ====================================================================
# Origination & disbursement
# ====================================================================
@transaction.atomic
def originate_loan(
    *,
    member,
    principal: Decimal,
    term_months: int,
    monthly_rate: Decimal,
    maker_user,
    purpose: str = "",
) -> Loan:
    """
    Create a DRAFT loan. Disbursement happens after pipeline certification.
    """
    principal = round_money(Decimal(str(principal)))
    monthly_rate = Decimal(str(monthly_rate))

    if principal <= 0:
        raise ValidationError("Principal must be positive.")
    if term_months <= 0:
        raise ValidationError("Term must be positive.")
    if monthly_rate < 0:
        raise ValidationError("Rate cannot be negative.")

    # Validate against AGM-configured range (if present)
    rate_range = get_active_value("loan_interest_rate_range")
    if rate_range:
        lo, hi = Decimal(str(rate_range["min"])), Decimal(str(rate_range["max"]))
        if not (lo <= monthly_rate <= hi):
            raise ValidationError(
                f"Rate {monthly_rate} outside approved range [{lo}, {hi}]."
            )

    loan = Loan.objects.create(
        member=member,
        principal_original=principal,
        principal_outstanding=principal,
        monthly_rate=monthly_rate,
        term_months=term_months,
        purpose=purpose,
        status=Loan.Status.DRAFT,
    )

    actor = create_pipeline(
        transaction_type="LOAN_DISBURSE",
        target_record_id=loan.id,
        maker_user=maker_user,
    )
    loan.pipeline_actor = actor
    loan.save(update_fields=["pipeline_actor"])
    return loan


# ====================================================================
# Manual repayment (variable, for irregular income)
# ====================================================================
@transaction.atomic
def repay_manual(
    *,
    loan: Loan,
    principal_paid: Decimal,
    interest_paid: Decimal,
    payment_date=None,
    maker_user,
) -> LoanRepayment:
    """
    Record a variable repayment with manual principal and interest.
    No hard validation on interest (see PRD Section 8.1).
    """
    payment_date = payment_date or today()
    principal_paid = round_money(Decimal(str(principal_paid)))
    interest_paid = round_money(Decimal(str(interest_paid)))

    if principal_paid < 0 or interest_paid < 0:
        raise ValidationError("Amounts cannot be negative.")
    if principal_paid == 0 and interest_paid == 0:
        raise ValidationError("At least one amount must be positive.")
    if principal_paid > loan.principal_outstanding:
        raise ValidationError("Principal paid exceeds outstanding balance.")
    if loan.status != Loan.Status.DISBURSED:
        raise ValidationError("Loan is not in a repayable state.")

    total_cash = principal_paid + interest_paid

    repayment = LoanRepayment.objects.create(
        loan=loan,
        principal_paid=principal_paid,
        interest_paid=interest_paid,
        payment_date=payment_date,
        mode="MANUAL",
        status=LoanRepayment.Status.PENDING_CHECK,
    )

    lines = [(CASH, "DEBIT", total_cash)]
    if interest_paid > 0:
        lines.append((INTEREST_INCOME, "CREDIT", interest_paid, loan.member))
    if principal_paid > 0:
        lines.append((LOANS_RECEIVABLE, "CREDIT", principal_paid, loan.member))

    je = post_journal_entry(
        description=f"Manual repayment – loan {loan.id}",
        lines=lines,
        created_by=maker_user,
        entry_date=payment_date,
    )
    repayment.journal_entry = je
    repayment.save(update_fields=["journal_entry"])

    actor = create_pipeline(
        transaction_type="LOAN_REPAY",
        target_record_id=repayment.id,
        maker_user=maker_user,
    )
    repayment.pipeline_actor = actor
    repayment.save(update_fields=["pipeline_actor"])
    return repayment


# ====================================================================
# Scheduled installment waterfall
# ====================================================================
@transaction.atomic
def repay_scheduled(
    *,
    loan: Loan,
    cash_amount: Decimal,
    scheduled_principal: Decimal,
    payment_date=None,
    maker_user,
) -> LoanRepayment:
    """
    Waterfall: interest due → scheduled principal → obligatory savings → voluntary.
    Reject if cash < interest due.
    """
    payment_date = payment_date or today()
    cash_amount = round_money(Decimal(str(cash_amount)))
    scheduled_principal = round_money(Decimal(str(scheduled_principal)))

    interest_due = round_money(loan.principal_outstanding * loan.monthly_rate)

    if cash_amount < interest_due:
        raise ValidationError("INSUFFICIENT_FOR_INTEREST_DUE")
    if loan.status != Loan.Status.DISBURSED:
        raise ValidationError("Loan is not in a repayable state.")

    remaining = cash_amount - interest_due
    principal_portion = min(remaining, scheduled_principal)
    remaining -= principal_portion

    # Savings allocation (only if a monthly cap is configured)
    cap = get_active_value("obligatory_savings_monthly_cap", as_of=payment_date)
    cap = Decimal(str(cap)) if cap is not None else Decimal("0")
    obligatory_portion = min(remaining, cap)
    remaining -= obligatory_portion
    voluntary_portion = remaining

    repayment = LoanRepayment.objects.create(
        loan=loan,
        principal_paid=principal_portion,
        interest_paid=interest_due,
        payment_date=payment_date,
        mode="SCHEDULED",
        status=LoanRepayment.Status.PENDING_CHECK,
    )

    lines = [(CASH, "DEBIT", cash_amount)]
    if interest_due > 0:
        lines.append((INTEREST_INCOME, "CREDIT", interest_due, loan.member))
    if principal_portion > 0:
        lines.append((LOANS_RECEIVABLE, "CREDIT", principal_portion, loan.member))
    if obligatory_portion > 0:
        lines.append((KAPITAL_SOSIAL, "CREDIT", obligatory_portion, loan.member))
    if voluntary_portion > 0:
        lines.append((VOLUNTARY_DEPOSIT, "CREDIT", voluntary_portion, loan.member))

    je = post_journal_entry(
        description=f"Scheduled installment – loan {loan.id}",
        lines=lines,
        created_by=maker_user,
        entry_date=payment_date,
    )
    repayment.journal_entry = je
    repayment.save(update_fields=["journal_entry"])

    actor = create_pipeline(
        transaction_type="LOAN_REPAY",
        target_record_id=repayment.id,
        maker_user=maker_user,
    )
    repayment.pipeline_actor = actor
    repayment.save(update_fields=["pipeline_actor"])
    return repayment
