from django.db import migrations

SEED = [
    ("40200", "Entrance Fee Income", "REVENUE", None),
]


def forwards(apps, schema_editor):
    Account = apps.get_model("accounting", "Account")
    for code, name, atype, parent in SEED:
        Account.objects.update_or_create(
            account_code=code,
            defaults={
                "account_name": name,
                "account_type": atype,
                "parent_account_code": parent,
                "status": "ACTIVE",
            },
        )


def backwards(apps, schema_editor):
    Account = apps.get_model("accounting", "Account")
    Account.objects.filter(account_code__in=[row[0] for row in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("accounting", "0003_alter_account_options_and_more")]
    operations = [migrations.RunPython(forwards, backwards)]
