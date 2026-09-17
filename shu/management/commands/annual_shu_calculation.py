from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from shu.services.calculation import run_shu_calculation, compute_member_payouts


class Command(BaseCommand):
    help = "Run annual SHU calculation for a fiscal year."

    def add_arguments(self, parser):
        parser.add_argument("--fy", type=str, required=True)
        parser.add_argument("--maker", type=str, required=True, help="UserProfile UUID")

    def handle(self, *args, **opts):
        calc = run_shu_calculation(opts["fy"], maker_user_id=opts["maker"])
        compute_member_payouts(calc)
        self.stdout.write(self.style.SUCCESS(f"Calculation {calc.id} created (DRAFT)."))
