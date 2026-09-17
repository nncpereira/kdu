# ledger/signals.py
from django.dispatch import Signal

# Fired after a JournalEntry is certified.
# kwargs:
#   journal_entry: JournalEntry instance (with .lines)
#   certified_by: UserProfile

journal_entry_certified = Signal()  # kwargs: journal_entry, certified_by
