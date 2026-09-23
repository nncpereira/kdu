from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from members.models import Member

DORMANCY_DAYS = 365


class Command(BaseCommand):
    help = "Mark ACTIVE members with no transactions for 12 months as DORMANT."

    def handle(self, *args, **opts):
        cutoff = timezone.now() - timedelta(days=DORMANCY_DAYS)
        qs = Member.objects.filter(
            status=Member.Status.ACTIVE,
        ).filter(
            last_transaction_at__lt=cutoff,
        )
        updated = qs.update(status=Member.Status.DORMANT, updated_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(f"Marked {updated} members DORMANT."))
