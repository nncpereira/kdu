import secrets
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.services import round_money, today
from governance.services import get_active_value
from ledger.services import post_journal_entry, account_net_balance
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
    maker_user,
) -> Member:
    """
    Create a PENDING member. The initial capital payment is a separate
    deposit step; capital balance starts at zero until that deposit is certified.
    """
    if not first_name or not last_name:
        raise ValidationError("First and last name are required.")

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
    )
    return member


@transaction.atomic
def pay_initial_capital(*, member, amount, maker_user, entry_date=None) -> MemberOnboarding:
    """
    First capital contribution. Enforces the US$50 minimum.
    Only allowed while member is PENDING.
    """
    entry_date = entry_date or today()
    amount = round_money(Decimal(str(amount)))

    if member.status != Member.Status.PENDING:
        raise ValidationError("Initial capital is only payable for PENDING members.")
    if amount < MIN_MEMBER_CAPITAL:
        raise ValidationError(
            f"MIN_CAPITAL_50_USD_REQUIRED: minimum is {MIN_MEMBER_CAPITAL}."
        )

    # Post a DRAFT journal entry: Dr Cash, Cr Kapital Sosial
    je = post_journal_entry(
        description=f"Initial capital for {member.membership_number}",
        lines=[
            ("1001", "DEBIT", amount),
            ("3101", "CREDIT", amount, member),
        ],
        created_by=maker_user,
        entry_date=entry_date,
    )

    actor = create_pipeline(
        transaction_type="MEMBER_ONBOARD",
        target_record_id=member.id,
        maker_user=maker_user,
    )

    # Store the JE reference on the pipeline actor target via a lightweight
    # transaction record would be cleaner, but for this demo we stash the JE id
    # on the pipeline actor target (see note below).
    # In production, use an explicit MemberOnboarding record.
    onboarding = MemberOnboarding.objects.create(
        member=member,
        initial_capital_amount=amount,
        journal_entry=je,
        pipeline_actor=actor,
        status=MemberOnboarding.Status.PENDING_CHECK,
    )
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
def request_exit(*, member, maker_user, entry_date=None) -> MemberExitRequest:
    """
    Checks obligations, posts a DRAFT refund entry, and creates the pipeline.
    Refund is posted to the member's capital account (3101) contra cash.
    """
    from loans.models import Loan

    entry_date = entry_date or today()

    if member.status != Member.Status.ACTIVE:
        raise ValidationError("Only ACTIVE members can exit.")
    if member.kapital_sosial_balance <= 0:
        raise ValidationError("Member has no capital to refund.")

    # Outstanding loan check
    active_loans = Loan.objects.filter(
        member=member,
        status__in=[Loan.Status.DISBURSED],
    )
    if active_loans.exists():
        raise ValidationError("MEMBER_HAS_OUTSTANDING_OBLIGATIONS")

    refund_amount = member.kapital_sosial_balance

    # Post DRAFT refund JE: Dr Kapital Sosial, Cr Cash
    je = post_journal_entry(
        description=f"Capital refund on exit – {member.membership_number}",
        lines=[
            ("3101", "DEBIT", refund_amount, member),
            ("1001", "CREDIT", refund_amount),
        ],
        created_by=maker_user,
        entry_date=entry_date,
    )

    actor = create_pipeline(
        transaction_type="MEMBER_EXIT",
        target_record_id=member.id,
        maker_user=maker_user,
    )

    exit_request = MemberExitRequest.objects.create(
        member=member,
        refund_amount=refund_amount,
        journal_entry=je,
        pipeline_actor=actor,
        status=MemberExitRequest.Status.PENDING_CHECK,
    )
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
