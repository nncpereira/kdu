from ledger.services import UnbalancedEntryError, post_journal_entry
from users.models import UserProfile

maker = UserProfile.objects.filter(role="MAKER").first()
if maker is None:
    raise RuntimeError(
        "No MAKER profile found. Run: python manage.py loaddata staff_users.json"
    )

# Balanced – should succeed
entry = post_journal_entry(
    description="Balance OK",
    lines=[("1001", "DEBIT", 100), ("3101", "CREDIT", 100)],
    created_by=maker,
)
print("OK: Balanced entry created.")

# Unbalanced – should raise UnbalancedEntryError before an entry is written
try:
    post_journal_entry(
        description="Broken",
        lines=[("1001", "DEBIT", 100), ("3101", "CREDIT", 90)],
        created_by=maker,
    )
except UnbalancedEntryError as e:
    print("OK:", e)
else:
    raise AssertionError("An unbalanced entry was incorrectly accepted.")
