from decimal import Decimal

import pytest

from apps.accounts.models import User
from apps.loans.models import AuditEvent, LoanApplication
from apps.orchestration.handlers import HANDLERS
from apps.orchestration.queue import JobQueue
from apps.orchestration.worker import Worker


@pytest.mark.django_db
def test_invalid_document_that_skipped_the_api_is_rejected_with_a_reason():
    application = LoanApplication.objects.create(
        country="ES",
        amount=Decimal("15000"),
        currency="EUR",
        monthly_income=Decimal("3000"),
        full_name="Ana Pérez",
        document="12345678A",  # wrong control letter, inserted without the API
        created_by=User.objects.create_user(username="creator"),
    )
    worker = Worker(JobQueue("w1"), HANDLERS)

    while worker.run_once():
        pass

    application.refresh_from_db()
    assert application.status == "REJECTED"
    rejection = AuditEvent.objects.filter(application_id=application.id).latest("id")
    assert rejection.data["reason"] == "Invalid control letter."
