"""Job queue on PostgreSQL. Callers only see this interface, so the transport can change."""

import random
from datetime import timedelta

from django.db import transaction
from django.db.models import F, Q
from django.db.models.functions import Now

from .models import Job

MAX_BACKOFF_SECONDS = 300


class JobQueue:
    def __init__(self, worker_id: str, queue: str = "default", lease_seconds: int = 60):
        self.worker_id = worker_id
        self.queue = queue
        self.lease_seconds = lease_seconds

    def claim(self, limit: int = 1) -> list[Job]:
        # Now() is the database clock, so every worker compares against the same time.
        ready = Q(status=Job.Status.PENDING, run_at__lte=Now())
        expired = Q(status=Job.Status.RUNNING, locked_until__lt=Now())

        with transaction.atomic():
            # Poison jobs: their worker died holding them too many times.
            Job.objects.filter(expired, queue=self.queue, attempts__gte=F("max_attempts")).update(
                status=Job.Status.DEAD, last_error="lease expired too many times"
            )
            # SKIP LOCKED: two workers never get the same job, and neither waits for the other.
            # The rows stay locked until the transaction ends, so nobody can take them meanwhile.
            ids = list(
                Job.objects.select_for_update(skip_locked=True)
                .filter(ready | expired, queue=self.queue)
                .order_by("run_at")
                .values_list("id", flat=True)[:limit]
            )
            Job.objects.filter(id__in=ids).update(
                status=Job.Status.RUNNING,
                attempts=F("attempts") + 1,
                locked_by=self.worker_id,
                locked_until=Now() + timedelta(seconds=self.lease_seconds),
            )
            return list(Job.objects.filter(id__in=ids).order_by("run_at"))

    def complete(self, job: Job) -> bool:
        return self._finish(job, status=Job.Status.DONE)

    def fail(self, job: Job, error: str) -> bool:
        if job.attempts >= job.max_attempts:
            return self._finish(job, status=Job.Status.DEAD, last_error=error)
        return self._finish(
            job,
            status=Job.Status.PENDING,
            run_at=Now() + _backoff(job.attempts),
            last_error=error,
        )

    def _finish(self, job: Job, **fields) -> bool:
        # Only if this worker still holds the job: a late result must not overwrite a new owner's.
        updated = Job.objects.filter(
            id=job.id, status=Job.Status.RUNNING, locked_by=self.worker_id
        ).update(locked_by="", locked_until=None, **fields)
        return updated == 1


def _backoff(attempts: int) -> timedelta:
    # Jitter: retries spread out instead of all hitting at once.
    seconds = min(2**attempts, MAX_BACKOFF_SECONDS)
    return timedelta(seconds=seconds * random.uniform(1, 1.5))
