from decimal import Decimal

import pytest

from apps.accounts.models import User
from apps.loans.models import AuditEvent, LoanApplication
from apps.orchestration.handlers import HANDLERS
from apps.orchestration.queue import JobQueue
from apps.orchestration.worker import Worker


@pytest.fixture
def spanish_bank(live_server, settings):
    # A real HTTP server running the simulator, so the agent makes a real request.
    settings.ES_BANK_URL = f"{live_server.url}/simulators/es/bank-profile"


@pytest.mark.django_db(transaction=True)
def test_application_goes_through_the_flow_on_its_own(spanish_bank):
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
    assert application.bank_profile == {"monthly_debt_payments": "1176.96"}
    assert "was approved" in application.explanation
    assert "Ana" not in application.explanation and "12345678Z" not in application.explanation
    trail = AuditEvent.objects.filter(application_id=application.id).order_by("id")
    assert [(e.data["to"], e.data["agent"]) for e in trail] == [
        ("CREATED", None),
        ("FETCHING_BANK_DATA", "intake"),
        ("EVALUATING", "banking"),
        ("APPROVED", "risk"),
    ]
