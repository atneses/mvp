import pytest

from apps.orchestration.models import Job
from apps.orchestration.queue import JobQueue
from apps.orchestration.worker import Worker


def _boom(job):
    raise RuntimeError("provider down")


@pytest.mark.django_db
def test_a_failing_job_is_retried_and_does_not_stop_the_others():
    ok = Job.objects.create(kind="ok")
    failing = Job.objects.create(kind="boom")
    worker = Worker(JobQueue("w1"), {"ok": lambda job: None, "boom": _boom})

    assert worker.run_once() == 2

    ok.refresh_from_db()
    failing.refresh_from_db()
    assert ok.status == "done"
    assert failing.status == "pending"
    assert "provider down" in failing.last_error
