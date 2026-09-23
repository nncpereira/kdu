from decimal import Decimal

from django.db import migrations, models


def backfill_savings_sweep(apps, schema_editor):
    """
    SCHEDULED repayments made before these fields existed already swept
    leftover cash into the member's Kapital Sosial (3101) and Voluntary
    (2101) accounts via their journal entry -- reconstruct the amounts
    from those journal lines so existing history isn't lost.
    """
    LoanRepayment = apps.get_model("loans", "LoanRepayment")
    JournalTransactionLine = apps.get_model("ledger", "JournalTransactionLine")

    for repayment in LoanRepayment.objects.filter(
        mode="SCHEDULED", journal_entry__isnull=False
    ):
        lines = JournalTransactionLine.objects.filter(
            journal_entry_id=repayment.journal_entry_id,
            entry_type="CREDIT",
            account_code__in=["3101", "2101"],
        )
        obligatory = Decimal("0.00")
        voluntary = Decimal("0.00")
        for line in lines:
            if line.account_code == "3101":
                obligatory += line.amount
            elif line.account_code == "2101":
                voluntary += line.amount

        if obligatory or voluntary:
            repayment.obligatory_portion = obligatory
            repayment.voluntary_portion = voluntary
            repayment.save(update_fields=["obligatory_portion", "voluntary_portion"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("loans", "0002_alter_loanrepayment_status"),
        ("ledger", "0005_reversalrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="loanrepayment",
            name="obligatory_portion",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=18
            ),
        ),
        migrations.AddField(
            model_name="loanrepayment",
            name="voluntary_portion",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=18
            ),
        ),
        migrations.RunPython(backfill_savings_sweep, noop_reverse),
    ]
