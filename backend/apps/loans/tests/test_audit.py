import pytest
from django.db import DatabaseError, connection, transaction

from apps.loans.models import AuditEvent


@pytest.mark.parametrize(
    "statement", ["UPDATE audit_events SET event = 'x'", "DELETE FROM audit_events"]
)
@pytest.mark.django_db
def test_audit_events_cannot_be_changed_or_deleted(statement):
    AuditEvent.objects.create(event="pii_access")

    with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(statement)

    assert AuditEvent.objects.get().event == "pii_access"
