from django.core.management.base import BaseCommand
from shu.models import ShuFiscalYear
from shu.services.snapshot import aggregate_annual_weighting


class Command(BaseCommand):
    help = "Aggregate SHU weighting base for a fiscal year."

    def add_arguments(self, parser):
        parser.add_argument("--fy", type=str, required=True, help="ShuFiscalYear UUID")

    def handle(self, *args, **opts):
        fy = ShuFiscalYear.objects.get(pk=opts["fy"])
        count = aggregate_annual_weighting(fy)
        self.stdout.write(self.style.SUCCESS(f"Aggregated {count} member rows."))
