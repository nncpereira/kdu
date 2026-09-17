from django.db import migrations

PARAMETER_KEY = "obligatory_savings_monthly_cap"


def forwards(apps, schema_editor):
    """
    0002_seed_default_config seeded this key as {"value": 20}, but every
    consumer (savings.services, loans.services) does
    Decimal(str(get_active_value(...))) expecting a bare number, which
    raises decimal.InvalidOperation on the dict. Unwrap any rows still
    shaped that way.
    """
    GlobalConfig = apps.get_model("governance", "GlobalConfig")
    for row in GlobalConfig.objects.filter(parameter_key=PARAMETER_KEY):
        value = row.parameter_value
        if isinstance(value, dict) and "value" in value:
            row.parameter_value = value["value"]
            row.save(update_fields=["parameter_value"])


def backwards(apps, schema_editor):
    GlobalConfig = apps.get_model("governance", "GlobalConfig")
    for row in GlobalConfig.objects.filter(parameter_key=PARAMETER_KEY):
        value = row.parameter_value
        if not isinstance(value, dict):
            row.parameter_value = {"value": value}
            row.save(update_fields=["parameter_value"])


class Migration(migrations.Migration):
    dependencies = [
        ("governance", "0002_seed_default_config"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
