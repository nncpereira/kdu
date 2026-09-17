from django.db import DatabaseError, connection, transaction

from ledger.models import JournalEntry
from ledger.services import certify_journal_entry, post_journal_entry
from users.models import UserProfile

maker = UserProfile.objects.filter(role="MAKER").first()
certifier = UserProfile.objects.filter(role="CERTIFIER").first()
if maker is None or certifier is None:
    raise RuntimeError(
        "MAKER and CERTIFIER profiles are required. "
        "Run: python manage.py loaddata staff_users.json"
    )

with transaction.atomic():
    entry = post_journal_entry(
        description="Immutability check",
        lines=[("1001", "DEBIT", 100), ("3101", "CREDIT", 100)],
        created_by=maker,
    )
    certify_journal_entry(entry, certifier)

    # Run the deferred balance check before rolling back the test data.
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    try:
        # A savepoint lets us inspect the record after the expected DB error.
        with transaction.atomic():
            entry.description = "tamper"
            entry.save(update_fields=["description"])
    except DatabaseError as exc:
        if "Immutability violation" not in str(exc):
            raise
        print("OK: Editing a certified journal entry was blocked.")
    else:
        raise AssertionError("A certified journal entry was incorrectly modified.")

    entry.refresh_from_db()
    assert entry.status == JournalEntry.Status.CERTIFIED
    assert entry.description == "Immutability check"
    transaction.set_rollback(True)

print("OK: Test completed; test records rolled back.")
