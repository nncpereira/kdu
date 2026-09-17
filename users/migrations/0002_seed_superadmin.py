from django.db import migrations


def forwards(apps, schema_editor):
    """
    Create a SUPERADMIN user if none exists yet.
    Uses the FIRST_SUPERADMIN_USERNAME / _PASSWORD env vars if present.
    Otherwise falls back to "admin" / "admin123" (dev only — MUST change).
    """
    import os
    from django.contrib.auth.hashers import make_password

    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("users", "UserProfile")

    if UserProfile.objects.filter(role="SUPERADMIN").exists():
        return

    username = os.environ.get("FIRST_SUPERADMIN_USERNAME", "admin")
    password = os.environ.get("FIRST_SUPERADMIN_PASSWORD", "admin123")

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "password": make_password(password),
            "is_staff": True,
            "is_superuser": True,
            "email": "admin@example.com",
        },
    )
    if created:
        UserProfile.objects.create(
            user=user,
            role="SUPERADMIN",
            must_change_password=True,
        )


def backwards(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    UserProfile.objects.filter(role="SUPERADMIN").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(forwards, backwards)]
