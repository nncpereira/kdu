from django.db import migrations
from decimal import Decimal

DEFAULTS = [
    (
        "obligatory_savings_monthly_cap",
        {"value": 20},  # stored as JSON
        "2025-01-01",
    ),
    (
        "loan_interest_rate_range",
        {"min": 0.01, "max": 0.02},
        "2025-01-01",
    ),
    # shu_split is intentionally NOT seeded — it must be set explicitly
    # by the cooperative before the first SHU calculation. This prevents an
    # accidental default split from being applied.
]


def forwards(apps, schema_editor):
    GlobalConfig = apps.get_model("governance", "GlobalConfig")
    UserProfile = apps.get_model("users", "UserProfile")

    # We need a creator. If no user exists yet, skip seeding.
    creator = UserProfile.objects.first()
    if creator is None:
        return

    for key, value, effective in DEFAULTS:
        GlobalConfig.objects.update_or_create(
            parameter_key=key,
            effective_from=effective,
            defaults={
                "parameter_value": value,
                "status": "ACTIVE",
                "created_by": creator,
            },
        )


def backwards(apps, schema_editor):
    GlobalConfig = apps.get_model("governance", "GlobalConfig")
    GlobalConfig.objects.filter(parameter_key__in=[row[0] for row in DEFAULTS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("governance", "0001_initial"),
        ("users", "0001_initial"),
    ]
    operations = [migrations.RunPython(forwards, backwards)]
