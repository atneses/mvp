"""Job queue in PostgreSQL. Defaults live in the database: a trigger also inserts jobs."""

from django.db import models
from django.db.models import Q
from django.db.models.functions import Now


class Job(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        RUNNING = "running"
        DONE = "done"
        DEAD = "dead"

    id = models.BigAutoField(primary_key=True)
    queue = models.CharField(max_length=32, db_default="default")
    kind = models.CharField(max_length=64)
    application = models.ForeignKey(
        "loans.LoanApplication", null=True, on_delete=models.CASCADE, related_name="jobs"
    )
    payload = models.JSONField(db_default={})
    status = models.CharField(max_length=16, choices=Status.choices, db_default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(db_default=0)
    max_attempts = models.PositiveSmallIntegerField(db_default=5)
    run_at = models.DateTimeField(db_default=Now())
    # Lease: if the worker dies, the job is claimed again once locked_until passes.
    locked_by = models.CharField(max_length=64, db_default="")
    locked_until = models.DateTimeField(null=True)
    last_error = models.TextField(db_default="")
    # NULL when there is no key: a unique index allows many NULLs but only one "".
    dedupe_key = models.CharField(max_length=200, null=True)  # noqa: DJ001
    correlation_id = models.CharField(max_length=64, db_default="")
    created_at = models.DateTimeField(db_default=Now())

    class Meta:
        db_table = "jobs"
        indexes = [
            models.Index(
                fields=["queue", "run_at"],
                condition=Q(status="pending"),
                name="jobs_pending_ready",
            ),
            models.Index(
                fields=["locked_until"],
                condition=Q(status="running"),
                name="jobs_running_lease",
            ),
        ]
        constraints = [
            # Not unique=True: Django would add an extra LIKE index, slowing every insert.
            models.UniqueConstraint(fields=["dedupe_key"], name="jobs_dedupe_key_unique"),
        ]

    def __str__(self):
        return f"{self.kind} #{self.id} {self.status}"
