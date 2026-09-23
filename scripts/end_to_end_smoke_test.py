from decimal import Decimal

from members.models import Member
from pipeline.services import certify, check
from savings.services import deposit
from users.models import UserProfile

maker = UserProfile.objects.get(role="MAKER")
checker = UserProfile.objects.get(role="CHECKER")
certifier = UserProfile.objects.get(role="CERTIFIER")

maria = Member.objects.get(membership_number="KDU-000001")

txn = deposit(member=maria, amount=Decimal("1000.00"), maker_user=maker)
check(txn.pipeline_actor, checker)
certify(txn.pipeline_actor, certifier)

maria.refresh_from_db()
print("Kapital Sosial:", maria.kapital_sosial_balance)  # 70.00 (50 + 20)
print("Voluntary   :", maria.voluntary_deposit.balance_available)  # 980.00
