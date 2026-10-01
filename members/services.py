from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from core.services import round_money, today
from ledger.services import post_journal_entry
from members.models import Member, MemberExitRequest, MemberOnboarding
from pipeline.services import create_pipeline

User = get_user_model()


@transaction.atomic
def provision_member_user(member: Member) -> User:
    """
    Create a Django auth user for a member to enable self-service login.
    Username = membership_number.
    A one-time password is generated; the member must change it on first login.
    Idempotent — if a user is already linked, return it.
    """
    if member.user_id:
        return member.user

    from users.services import create_member_user

    user = create_member_user(
        member=member,
        email=member.email or "",
        first_name=member.first_name,
        last_name=member.last_name,
    )

    # Hand the temp password back to the caller (e.g., to send via SMS).
    return user


MIN_MEMBER_CAPITAL = Decimal("50.00")  # DL 76/2022, Art. 19
MIN_COOP_CAPITAL = Decimal("5000.00")  # DL 76/2022, Art. 18

# Board-approved amounts collected upfront from every new member (total $175):
#   Principal savings (one-time capital)      $150
#   First month's mandatory/obligatory saving   $20
#   Entrance/admin/booklet fee (non-refundable)  $5
STANDARD_INITIAL_CAPITAL = Decimal("150.00")
STANDARD_FIRST_MONTH_SAVINGS = Decimal("20.00")
STANDARD_ENTRANCE_FEE = Decimal("5.00")

ENTRANCE_FEE_INCOME = "40200"


# ====================================================================
# Onboarding
# ====================================================================
@transaction.atomic
def onboard_member(
    *,
    first_name,
    last_name,
    national_id=None,
    phone_number="",
    date_of_birth=None,
    aldeia="",
    suco="",
    posto="",
    municipio="",
    profession="",
    middle_name="",
    salutation="Mr",
    email=None,
    endorser_1: Member,
    endorser_2: Member,
    maker_user,
) -> Member:
    """
    Create a PENDING member. The initial capital payment is a separate
    deposit step; capital balance starts at zero until that deposit is certified.
    """
    if not first_name or not last_name:
        raise ValidationError("First and last name are required.")
    if today().month == 6:
        raise ValidationError(
            "NEW_MEMBERS_CLOSED_IN_JUNE: no new members are accepted in June, "
            "the last month of the fiscal year."
        )
    if endorser_1 is None or endorser_2 is None:
        raise ValidationError("Two endorsers are required to onboard a new member.")
    if endorser_1.id == endorser_2.id:
        raise ValidationError("The two endorsers must be different members.")
    if (
        endorser_1.status != Member.Status.ACTIVE
        or endorser_2.status != Member.Status.ACTIVE
    ):
        raise ValidationError("Endorsers must be active members.")

    member = Member.objects.create(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        salutation=salutation,
        national_id=national_id,
        phone_number=phone_number,
        email=email,
        date_of_birth=date_of_birth,
        aldeia=aldeia,
        suco=suco,
        posto=posto,
        municipio=municipio,
        profession=profession,
        status=Member.Status.PENDING,
        endorser_1=endorser_1,
        endorser_2=endorser_2,
    )
    return member


@transaction.atomic
def pay_initial_capital(
    *,
    member,
    amount,
    maker_user,
    entry_date=None,
    first_month_savings=Decimal("0"),
    entrance_fee=Decimal("0"),
):
    """
    Record the cash a new member brings upfront. `amount` is the one-time
    capital (Simpanan Pokok); `first_month_savings` and `entrance_fee` are
    optional on top of it (the standard onboarding flow passes the board-
    approved $20 / $5, but existing callers that only ever charged capital
    keep working unchanged since both default to zero).
    """
    entry_date = entry_date or today()
    amount = round_money(Decimal(str(amount)))
    first_month_savings = round_money(Decimal(str(first_month_savings)))
    entrance_fee = round_money(Decimal(str(entrance_fee)))

    if member.status != Member.Status.PENDING:
        raise ValidationError("Initial capital is only payable for PENDING members.")
    if amount < MIN_MEMBER_CAPITAL:
        raise ValidationError(
            f"MIN_CAPITAL_50_USD_REQUIRED: minimum is {MIN_MEMBER_CAPITAL}."
        )

    total_cash = amount + first_month_savings + entrance_fee
    lines = [("1001", "DEBIT", total_cash)]
    # Both capital and the first month's mandatory savings build the
    # member's own Kapital Sosial, same as a normal obligatory deposit.
    lines.append(("3101", "CREDIT", amount + first_month_savings, member))
    if entrance_fee > 0:
        lines.append((ENTRANCE_FEE_INCOME, "CREDIT", entrance_fee, member))

    je = post_journal_entry(
        description=f"Initial capital for {member.membership_number}",
        lines=lines,
        created_by=maker_user,
        entry_date=entry_date,
    )

    # Record the first month's savings as a normal Transaction too, so it
    # counts toward that month's obligatory cap like any other deposit.
    obligatory_txn = None
    if first_month_savings > 0:
        from savings.models import Transaction as SavingsTxn

        obligatory_txn = SavingsTxn.objects.create(
            member=member,
            transaction_type=SavingsTxn.Type.DEPOSIT,
            requested_amount=first_month_savings,
            obligatory_portion=first_month_savings,
            voluntary_portion=Decimal("0"),
            status=SavingsTxn.Status.PENDING_CHECK,
            journal_entry=je,
        )

    # 1. Create the onboarding record WITHOUT the pipeline actor.
    onboarding = MemberOnboarding.objects.create(
        member=member,
        initial_capital_amount=amount,
        first_month_savings_amount=first_month_savings,
        entrance_fee_amount=entrance_fee,
        obligatory_transaction=obligatory_txn,
        journal_entry=je,
        status=MemberOnboarding.Status.PENDING_CHECK,
    )

    # 2. Create the actor with target_record_id = onboarding.id.
    actor = create_pipeline(
        transaction_type="MEMBER_ONBOARD",
        target_record_id=onboarding.id,
        maker_user=maker_user,
    )

    # 3. Link them.
    onboarding.pipeline_actor = actor
    onboarding.save(update_fields=["pipeline_actor"])
    return onboarding


# ====================================================================
# Status transitions
# ====================================================================
@transaction.atomic
def activate_member(member: Member, certifier_user) -> Member:
    """Move a PENDING member to ACTIVE after onboarding has been certified."""
    if member.status != Member.Status.PENDING:
        raise ValidationError("Member is not PENDING.")
    if member.kapital_sosial_balance < MIN_MEMBER_CAPITAL:
        raise ValidationError(f"Cannot activate: capital below {MIN_MEMBER_CAPITAL}.")
    member.status = Member.Status.ACTIVE
    member.save(update_fields=["status", "updated_at"])
    return member


@transaction.atomic
def suspend_member(member: Member, reason: str = "") -> Member:
    if member.status == Member.Status.CLOSED:
        raise ValidationError("Closed members cannot be suspended.")
    member.status = Member.Status.SUSPENDED
    member.save(update_fields=["status", "updated_at"])
    return member


@transaction.atomic
def reactivate_member(member: Member) -> Member:
    if member.status not in (Member.Status.SUSPENDED, Member.Status.DORMANT):
        raise ValidationError("Only suspended or dormant members can be reactivated.")
    member.status = Member.Status.ACTIVE
    member.save(update_fields=["status", "updated_at"])
    return member


# ====================================================================
# Exit / capital refund
# ====================================================================
@transaction.atomic
def request_exit(*, member, maker_user, entry_date=None):
    from loans.models import Loan

    entry_date = entry_date or today()

    if member.status != Member.Status.ACTIVE:
        raise ValidationError("Only ACTIVE members can exit.")
    if member.kapital_sosial_balance <= 0:
        raise ValidationError("Member has no capital to refund.")
    if Loan.objects.filter(member=member, status=Loan.Status.DISBURSED).exists():
        raise ValidationError("MEMBER_HAS_OUTSTANDING_OBLIGATIONS")

    refund_amount = member.kapital_sosial_balance

    je = post_journal_entry(
        description=f"Capital refund on exit – {member.membership_number}",
        lines=[
            ("3101", "DEBIT", refund_amount, member),
            ("1001", "CREDIT", refund_amount),
        ],
        created_by=maker_user,
        entry_date=entry_date,
    )

    exit_request = MemberExitRequest.objects.create(
        member=member,
        refund_amount=refund_amount,
        journal_entry=je,
        status=MemberExitRequest.Status.PENDING_CHECK,
    )

    actor = create_pipeline(
        transaction_type="MEMBER_EXIT",
        target_record_id=exit_request.id,
        maker_user=maker_user,
    )
    exit_request.pipeline_actor = actor
    exit_request.save(update_fields=["pipeline_actor"])
    return exit_request


@transaction.atomic
def warn_if_capital_below_minimum() -> dict:
    """Report whether the cooperative is below the $5,000 legal minimum."""
    total = sum(
        (
            m.kapital_sosial_balance
            for m in Member.objects.filter(status=Member.Status.ACTIVE)
        ),
        Decimal("0"),
    )
    return {
        "total_kapital_sosial": total,
        "below_minimum": total < MIN_COOP_CAPITAL,
        "minimum": MIN_COOP_CAPITAL,
    }
