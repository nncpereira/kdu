from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = (
        "Load one or more fixtures inside a transaction with "
        "app.ledger_posting enabled, so fixtures may set guarded "
        "balance columns (members.kapital_sosial_balance, "
        "savings.balance_available, savings.balance_held_pipeline) "
        "without tripping guard_balance_update()."
    )

    def add_arguments(self, parser):
        parser.add_argument("fixture_labels", nargs="+")

    def handle(self, *args, **opts):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.ledger_posting = 'true'")
            call_command("loaddata", *opts["fixture_labels"])
