from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.loans.models import AuditEvent, LoanApplication
from apps.orchestration.handlers import HANDLERS
from apps.orchestration.models import Job
from apps.orchestration.queue import JobQueue
from apps.orchestration.worker import Worker


@pytest.mark.django_db
def test_application_fails_when_its_bank_never_answers_and_an_admin_retries_it(settings):
    settings.ES_BANK_URL = "http://127.0.0.1:9/down"  # nothing listens here
    application = LoanApplication.objects.create(
        country="ES",
        amount=Decimal("15000"),
        currency="EUR",
        monthly_income=Decimal("3000"),
        full_name="Ana Pérez",
        document="12345678Z",
        created_by=User.objects.create_user(username="creator"),
    )
    worker = Worker(JobQueue("w1"), HANDLERS)
    worker.run_once()  # intake passes; the bank step is next
    Job.objects.filter(status="pending").update(max_attempts=1)  # its last attempt

    worker.run_once()

    application.refresh_from_db()
    assert application.status == "FAILED"
    assert "Connection refused" in AuditEvent.objects.latest("id").data["reason"]

    admin = APIClient()
    admin.force_authenticate(
        User.objects.create_user(username="admin", role="admin", allowed_countries=["ES"])
    )
    response = admin.patch(
        f"/api/loan-applications/{application.id}/status",
        {"to": "CREATED", "reason": "bank is back", "expected_version": application.version},
        format="json",
    )

    assert response.status_code == 200
    assert Job.objects.filter(application_id=application.id, status="pending").exists()
