from django.db import models

from core.models import UUIDTimeStampedModel


class ShuFiscalYear(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    year_start = models.DateField()
    year_end = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    net_surplus = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    kapital_sosial = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    accumulated_reserva_legal = models.DecimalField(
        max_digits=18, decimal_places=2, default=0
    )

    class Meta:
        ordering = ["-year_start"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(year_end__gt=models.F("year_start")),
                name="fy_end_after_start",
            ),
        ]

    def __str__(self):
        return f"FY {self.year_start}–{self.year_end} [{self.status}]"


class ShuCalculation(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        CERTIFIED = "CERTIFIED", "Certified"
        PAYOUT_COMPLETE = "PAYOUT_COMPLETE", "Payout Complete"
        REJECTED = "REJECTED", "Rejected"

    fy = models.ForeignKey(
        ShuFiscalYear, on_delete=models.PROTECT, related_name="calculations"
    )
    net_surplus = models.DecimalField(max_digits=18, decimal_places=2)
    reserva_legal_pct = models.DecimalField(max_digits=5, decimal_places=2)
    admin_fund_pct = models.DecimalField(max_digits=5, decimal_places=2)
    jasa_simpanan_pct = models.DecimalField(max_digits=5, decimal_places=2)
    jasa_bunga_pct = models.DecimalField(max_digits=5, decimal_places=2)

    # agm_resolution_id removed
    reserva_legal_amt = models.DecimalField(max_digits=18, decimal_places=2)
    admin_fund_amt = models.DecimalField(max_digits=18, decimal_places=2)
    jasa_simpanan_amt = models.DecimalField(max_digits=18, decimal_places=2)
    jasa_bunga_amt = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shu_calculations",
    )
    reserve_journal_entry = models.ForeignKey(
        "ledger.JournalEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shu_reserves",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["fy", "status"])]

    def __str__(self):
        return f"SHU {self.fy} – {self.status}"

    @property
    def total_allocated(self):
        return (
            self.reserva_legal_amt
            + self.admin_fund_amt
            + self.jasa_simpanan_amt
            + self.jasa_bunga_amt
        )


class ShuMemberMonthlyBalance(UUIDTimeStampedModel):
    """Month-end snapshot per member. Populated by snapshot job."""

    fy = models.ForeignKey(
        ShuFiscalYear, on_delete=models.CASCADE, related_name="monthly_balances"
    )
    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="shu_monthly_balances"
    )
    month_date = models.DateField()
    total_balance = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fy", "member", "month_date"], name="uq_shu_monthly"
            ),
        ]
        indexes = [models.Index(fields=["fy", "member"])]


class ShuWeightingBase(UUIDTimeStampedModel):
    """Per-member aggregated weighting data for a fiscal year."""

    fy = models.ForeignKey(
        ShuFiscalYear, on_delete=models.CASCADE, related_name="weighting_base"
    )
    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="shu_weighting"
    )
    sum_weighted_balance = models.DecimalField(max_digits=18, decimal_places=2)
    months_active = models.PositiveIntegerField()
    weighted_savings_units = models.DecimalField(max_digits=18, decimal_places=2)
    loan_interest_paid = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["fy", "member"], name="uq_shu_weighting"),
        ]
        indexes = [models.Index(fields=["fy"])]


class ShuMemberPayout(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PAID = "PAID", "Paid"

    calc = models.ForeignKey(
        ShuCalculation, on_delete=models.CASCADE, related_name="payouts"
    )
    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="shu_payouts"
    )
    jasa_simpanan_gross = models.DecimalField(max_digits=18, decimal_places=2)
    jasa_bunga_gross = models.DecimalField(max_digits=18, decimal_places=2)
    net_payout = models.DecimalField(max_digits=18, decimal_places=2)
    journal_entry = models.ForeignKey(
        "ledger.JournalEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="shu_payouts",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["calc", "member"], name="uq_shu_payout_per_member"
            ),
        ]
        indexes = [models.Index(fields=["calc", "status"])]

    def __str__(self):
        return f"Payout {self.member.membership_number} – {self.net_payout}"
