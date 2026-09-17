from django.db import DatabaseError, connection, transaction

from members.models import Member

m = Member.objects.first()
if m is None:
    raise RuntimeError(
        "No Member records found. Run: python manage.py loaddata test_members"
    )

m.kapital_sosial_balance = 0
try:
    m.save(update_fields=["kapital_sosial_balance"])
except DatabaseError as exc:
    if "Direct balance updates are forbidden" not in str(exc):
        raise
    print("OK:", exc)
else:
    raise AssertionError("An unguarded balance update was incorrectly allowed.")

# Legit path
with transaction.atomic():
    with connection.cursor() as c:
        c.execute("SET LOCAL app.ledger_posting = 'true'")
    m.save(update_fields=["kapital_sosial_balance"])

print("OK: Guarded balance update succeeded via the ledger posting flow.")
