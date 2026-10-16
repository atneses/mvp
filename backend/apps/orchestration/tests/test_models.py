import pytest
from django.db import connection

from apps.orchestration.models import Job


@pytest.mark.django_db
def test_plain_sql_insert_gets_the_database_defaults():
    # The trigger of step 24 inserts jobs with SQL, without Django's defaults.
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO jobs (kind) VALUES ('advance') RETURNING id")
        job_id = cursor.fetchone()[0]

    job = Job.objects.get(id=job_id)
    assert (job.queue, job.status, job.attempts, job.max_attempts) == ("default", "pending", 0, 5)
    assert job.run_at is not None
    assert job.payload == {}
