from decimal import Decimal

import pytest

from apps.accounts.models import User
from apps.loans.models import AuditEvent, LoanApplication
from apps.orchestration.handlers import HANDLERS
from apps.orchestration.queue import JobQueue
from apps.orchestration.worker import Worker


@pytest.mark.django_db
def test_application_goes_through_the_flow_on_its_own():
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

    while worker.run_once():
        pass

    application.refresh_from_db()
    assert application.status == "APPROVED"
    trail = AuditEvent.objects.filter(application_id=application.id).order_by("id")
    assert [(e.data["to"], e.data["agent"]) for e in trail] == [
        ("CREATED", None),
        ("FETCHING_BANK_DATA", "intake"),
        ("EVALUATING", "banking"),
        ("APPROVED", "risk"),
    ]
