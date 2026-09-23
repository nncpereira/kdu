from django.core.management.base import BaseCommand

from shu.services.snapshot import take_monthly_snapshot


class Command(BaseCommand):
    help = "Snapshot month-end savings balances for all active members."

    def handle(self, *args, **opts):
        count = take_monthly_snapshot()
        self.stdout.write(self.style.SUCCESS(f"Snapshotted {count} member rows."))
