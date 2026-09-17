from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from shu.services.calculation import run_shu_calculation


class Command(BaseCommand):
    help = "Run the SHU calculation for a fiscal year (creates DRAFT calc)."

    def add_arguments(self, parser):
        parser.add_argument("--fy", type=str, required=True, help="ShuFiscalYear UUID")
        parser.add_argument("--maker", type=str, required=True, help="UserProfile UUID")

    def handle(self, *args, **opts):
        calc = run_shu_calculation(opts["fy"], maker_user_id=opts["maker"])
        self.stdout.write(
            self.style.SUCCESS(f"Calculation {calc.id} created (PENDING_CHECK).")
        )
