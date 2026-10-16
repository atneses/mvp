"""Loan application: the request and its current state.

More columns (bank data, decision, explanation...) are added by the steps that use them.
"""

from uuid import uuid7

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Now

from countries.registry import country_choices


class LoanApplication(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED"
        FETCHING_BANK_DATA = "FETCHING_BANK_DATA"
        WAITING_BANK_CALLBACK = "WAITING_BANK_CALLBACK"
        EVALUATING = "EVALUATING"
        MANUAL_REVIEW = "MANUAL_REVIEW"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"
        CANCELLED = "CANCELLED"
        FAILED = "FAILED"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    country = models.CharField(max_length=2, choices=country_choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CREATED)
    # Optimistic locking: every change increments it; a stale version means a concurrent edit.
    version = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3)
    monthly_income = models.DecimalField(max_digits=18, decimal_places=2)
    full_name = models.CharField(max_length=200)
    # Normalized by the country plugin (e.g. "12345678Z"), so duplicates can be found.
    document = models.CharField(max_length=32)
    # Common format for every country's bank (see CountryPlugin.fetch_bank_profile).
    bank_profile = models.JSONField(null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "loan_applications"
        indexes = [
            models.Index(
                fields=["country", "status", "-created_at", "-id"],
                name="loan_country_status_created",
            ),
            models.Index(fields=["country", "-created_at", "-id"], name="loan_country_created"),
            models.Index(fields=["country", "document"], name="loan_country_document"),
        ]
        constraints = [
            # One active application per document and country; the database enforces it.
            # Final states (approved, rejected, cancelled) no longer block a new one.
            models.UniqueConstraint(
                fields=["country", "document"],
                condition=~Q(status__in=["APPROVED", "REJECTED", "CANCELLED"]),
                name="loan_one_active_per_document",
            ),
        ]

    def __str__(self):
        # No PII: this text can end up in logs and in the admin.
        return f"{self.country} {self.id} {self.status}"


class AuditEvent(models.Model):
    """Append-only history: a database trigger rejects any UPDATE or DELETE."""

    id = models.BigAutoField(primary_key=True)
    # No foreign keys: the history must outlive the rows it talks about.
    application_id = models.UUIDField(null=True)
    actor_id = models.BigIntegerField(null=True)
    event = models.CharField(max_length=64)
    data = models.JSONField(db_default={})
    correlation_id = models.CharField(max_length=64, db_default="")
    created_at = models.DateTimeField(db_default=Now())

    class Meta:
        db_table = "audit_events"
        indexes = [
            models.Index(fields=["application_id", "created_at"], name="audit_application_created"),
        ]

    def __str__(self):
        return f"{self.event} #{self.id}"
