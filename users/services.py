import re
import secrets
import unicodedata

from django.contrib.auth import get_user_model
from django.db import transaction

from audit.services import record_audit
from users.models import UserProfile

User = get_user_model()


def _slugify_name_part(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", value.lower())


def _generate_member_username(member) -> str:
    """
    Build a human-readable username from the member's name, e.g.
    "joao.soares". Falls back to the membership number if the name
    doesn't yield any usable characters. Appends a numeric suffix on
    collision.
    """
    first = _slugify_name_part(member.first_name)
    last = _slugify_name_part(member.last_name)
    base = f"{first}.{last}" if first and last else first or last
    base = base or member.membership_number.lower()

    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


# ====================================================================
# Staff provisioning
# ====================================================================
@transaction.atomic
def create_staff_user(*, username, password, role, email="", first_name="", last_name="", actor=None, request=None):
    """
    Create a staff user plus matching UserProfile in one transaction.
    """
    if role not in dict(UserProfile.Role.choices):
        raise ValueError(f"Unknown role: {role}")

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    profile = UserProfile.objects.create(user=user, role=role)

    if actor is not None:
        record_audit(
            actor=actor,
            action="USER_CREATED",
            target_type="USER",
            target_id=profile.id,
            target_repr=username,
            description=f"Created {role} user: {username}",
            metadata={"role": role, "email": email},
            request=request,
        )
    return profile


@transaction.atomic
def issue_temp_password(user, *, actor=None, request=None) -> str:
    """
    Force a password reset on the next login and return the temporary password.
    """
    temp = secrets.token_urlsafe(10)
    user.set_password(temp)
    user.save(update_fields=["password"])

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.must_change_password = True
    profile.save(update_fields=["must_change_password"])

    if actor is not None:
        profile = getattr(user, "profile", None)
        record_audit(
            actor=actor,
            action="USER_PASSWORD_RESET",
            target_type="USER",
            target_id=profile.id if profile else None,
            target_repr=user.username,
            description=f"Issued temporary password for: {user.username}",
            request=request,
        )

    return temp


# ====================================================================
# Member provisioning (used by members.services.provision_member_user)
# ====================================================================
@transaction.atomic
def create_member_user(*, member, email="", first_name="", last_name=""):
    """
    Create a MEMBER-role auth user for a member.
    Username is derived from the member's name (e.g. "joao.soares");
    a temp password is generated.
    """
    username = _generate_member_username(member)

    temp = secrets.token_urlsafe(10)
    user = User.objects.create_user(
        username=username,
        password=temp,
        email=email,
        first_name=first_name or member.first_name,
        last_name=last_name or member.last_name,
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.Role.MEMBER,
        must_change_password=True,
    )
    member.user = user
    member.save(update_fields=["user", "updated_at"])
    user._temp_password = temp
    return user


@transaction.atomic
def set_staff_active(
    profile: UserProfile, active: bool, *, actor=None, request=None
) -> UserProfile:
    """Enable or disable a staff user's ability to log in."""
    profile.user.is_active = active
    profile.user.save(update_fields=["is_active"])

    if actor is not None:
        record_audit(
            actor=actor,
            action="USER_ENABLED" if active else "USER_DISABLED",
            target_type="USER",
            target_id=profile.id,
            target_repr=profile.user.username,
            description=(
                f"{'Enabled' if active else 'Disabled'} user: "
                f"{profile.user.username}"
            ),
            request=request,
        )
    return profile


@transaction.atomic
def update_staff_profile(profile: UserProfile, **fields) -> UserProfile:
    """Update the linked auth user's editable fields."""
    user_fields = {}
    for key in ("first_name", "last_name", "email"):
        if key in fields:
            user_fields[key] = fields[key]
    if user_fields:
        for k, v in user_fields.items():
            setattr(profile.user, k, v)
        profile.user.save(update_fields=list(user_fields.keys()))
    return profile
