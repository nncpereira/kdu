from django.db import migrations

SEED = [
    # code, name, type, parent_code
    ("1001", "Cash on Hand", "ASSET", None),
    ("1301", "Loans Receivable", "ASSET", None),
    ("2101", "Member Voluntary Deposits", "LIABILITY", None),
    ("3101", "Kapital Sosial", "EQUITY", None),
    ("3200", "SHU Payable", "LIABILITY", None),
    ("3501", "Reserva Legal", "EQUITY", None),
    ("3502", "Admin & Operational Fund", "EQUITY", None),
    ("3900", "Retained Surplus", "EQUITY", None),
    ("40100", "Interest Income from Loans", "REVENUE", None),
    ("5101", "AGM Expense", "EXPENSE", None),
    ("5102", "Salaries Expense", "EXPENSE", None),
    ("5103", "Utilities Expense", "EXPENSE", None),
    ("5104", "Office Supplies Expense", "EXPENSE", None),
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
    dependencies = [("accounting", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
