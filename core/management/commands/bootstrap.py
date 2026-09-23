from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from users.models import UserProfile
from users.services import create_staff_user

User = get_user_model()


class Command(BaseCommand):
    help = "Bootstrap KDU: migrate, seed CoA, config, and default staff users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Force recreate staff users (destructive).",
        )
        parser.add_argument(
            "--with-members",
            action="store_true",
            help="Also load the test members fixture.",
        )

    def handle(self, *args, **opts):
        self.stdout.write("Running migrations…")
        call_command("migrate", interactive=False)

        # The chart of accounts is seeded by accounting.0002_seed_coa.
        # Loading the legacy fixture would bypass auto-managed timestamps.
        self.stdout.write("Chart of Accounts ready (seeded by migrations).")

        self.stdout.write("Loading default governance config…")
        # Ensure at least one superadmin exists before governance fixture
        if not UserProfile.objects.filter(role=UserProfile.Role.SUPERADMIN).exists():
            self.stdout.write("Creating superadmin…")
            create_staff_user(
                username="admin",
                password="admin123",
                role=UserProfile.Role.SUPERADMIN,
                email="admin@example.com",
                first_name="Super",
                last_name="Admin",
            )

        call_command("loaddata", "default_config")

        if (
            opts["fresh"]
            or not UserProfile.objects.filter(role=UserProfile.Role.MAKER).exists()
        ):
            self.stdout.write("Creating staff users…")
            for username, role, first, last in [
                ("maker1", UserProfile.Role.MAKER, "João", "Maker"),
                ("checker1", UserProfile.Role.CHECKER, "Maria", "Checker"),
                ("certifier1", UserProfile.Role.CERTIFIER, "Pedro", "Certifier"),
            ]:
                if User.objects.filter(username=username).exists():
                    continue
                create_staff_user(
                    username=username,
                    password="changeme123",
                    role=role,
                    first_name=first,
                    last_name=last,
                )

        if opts["with_members"]:
            self.stdout.write("Loading test members…")
            call_command("loadfixture", "test_members")

        self.stdout.write(self.style.SUCCESS("Bootstrap complete."))
        self.stdout.write(
            "Default passwords: admin123 / changeme123 — change immediately."
        )
