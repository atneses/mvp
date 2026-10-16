from decimal import Decimal

import pytest
from django.db import connection

from apps.accounts.models import User
from apps.loans.models import AuditEvent, LoanApplication
from apps.loans.services import change_status
from apps.orchestration.models import Job
from core.audit import audit_context


@pytest.fixture
def application(db):
    user = User.objects.create_user(username="creator")
    with audit_context(actor_id=user.id, correlation_id="req-1"):
        return LoanApplication.objects.create(
            country="ES",
            amount=Decimal("15000"),
            currency="EUR",
            monthly_income=Decimal("3000"),
            full_name="Ana Pérez",
            document="12345678Z",
            created_by=user,
        )


def test_each_status_change_creates_a_job_and_an_audit_row(application):
    with audit_context(actor_id=7, correlation_id="req-2", reason="manual check"):
        change_status(application, "VALIDATING", expected_version=1)

    jobs = Job.objects.filter(application=application).order_by("id")
    assert [(j.kind, j.dedupe_key, j.correlation_id) for j in jobs] == [
        ("advance", f"{application.id}:1", "req-1"),
        ("advance", f"{application.id}:2", "req-2"),
    ]
    last = AuditEvent.objects.filter(application_id=application.id).latest("id")
    assert last.event == "status_changed"
    assert last.actor_id == 7
    assert last.data == {
        "from": "CREATED",
        "to": "VALIDATING",
        "version": 2,
        "reason": "manual check",
    }


def test_same_version_does_not_create_a_second_job(application):
    # A status change that does not bump the version (e.g. a replayed write).
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE loan_applications SET status = 'CANCELLED' WHERE id = %s", [application.id]
        )

    assert Job.objects.filter(application=application).count() == 1
