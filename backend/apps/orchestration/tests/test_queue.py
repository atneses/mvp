import threading
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from apps.orchestration.models import Job
from apps.orchestration.queue import JobQueue


@pytest.mark.django_db(transaction=True)
def test_two_workers_never_take_the_same_job():
    Job.objects.bulk_create([Job(kind="advance") for _ in range(30)])
    taken = {"a": [], "b": []}
    start = threading.Barrier(2)

    def work(worker_id):
        queue = JobQueue(worker_id)
        start.wait()
        while jobs := queue.claim(limit=1):
            taken[worker_id] += [job.id for job in jobs]
        connection.close()

    threads = [threading.Thread(target=work, args=(w,)) for w in taken]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not set(taken["a"]) & set(taken["b"])
    assert len(taken["a"]) + len(taken["b"]) == 30


@pytest.mark.django_db
def test_expired_lease_is_claimed_by_another_worker():
    Job.objects.create(kind="advance")
    [job] = JobQueue("dead-worker").claim()
    Job.objects.filter(id=job.id).update(locked_until=timezone.now() - timedelta(seconds=1))

    [again] = JobQueue("other-worker").claim()

    assert again.id == job.id
    assert (again.locked_by, again.attempts) == ("other-worker", 2)
    assert JobQueue("dead-worker").complete(job) is False


@pytest.mark.django_db
def test_job_is_dead_after_max_attempts():
    Job.objects.create(kind="advance", max_attempts=2)
    queue = JobQueue("worker")

    [job] = queue.claim()
    queue.fail(job, "boom")
    assert queue.claim() == []  # backoff
    Job.objects.filter(id=job.id).update(run_at=timezone.now())
    [job] = queue.claim()
    queue.fail(job, "boom again")

    job.refresh_from_db()
    assert (job.status, job.attempts, job.last_error) == ("dead", 2, "boom again")
