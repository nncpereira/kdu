import secrets

from django.contrib.auth import get_user_model
from django.db import transaction

from users.models import UserProfile

User = get_user_model()


# ====================================================================
# Staff provisioning
# ====================================================================
@transaction.atomic
def create_staff_user(*, username, password, role, email="", first_name="", last_name=""):
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
    return profile


@transaction.atomic
def issue_temp_password(user) -> str:
    """
    Force a password reset on the next login and return the temporary password.
    """
    temp = secrets.token_urlsafe(10)
    user.set_password(temp)
    user.save(update_fields=["password"])

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.must_change_password = True
    profile.save(update_fields=["must_change_password"])
    return temp


# ====================================================================
# Member provisioning (used by members.services.provision_member_user)
# ====================================================================
@transaction.atomic
def create_member_user(*, member, email="", first_name="", last_name=""):
    """
    Create a MEMBER-role auth user for a member.
    Username is the membership number; a temp password is generated.
    """
    username = member.membership_number

    # Uniqueness guard
    if User.objects.filter(username=username).exists():
        username = f"{username}-{secrets.token_hex(3)}"

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
def set_staff_active(profile: UserProfile, active: bool) -> UserProfile:
    """Enable or disable a staff user's ability to log in."""
    profile.user.is_active = active
    profile.user.save(update_fields=["is_active"])
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
