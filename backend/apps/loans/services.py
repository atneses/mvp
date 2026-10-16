"""Business operations on loan applications, shared by the API and the orchestrator."""

from django.db.models import F
from django.utils import timezone

from .models import LoanApplication
from .states import check_transition


class VersionConflictError(Exception):
    """Someone else changed the application since it was read."""


def change_status(
    application: LoanApplication, target: str, expected_version: int, updates=None
) -> None:
    """Move the application to `target` if the transition is legal and nobody changed it.

    Raises InvalidTransitionError or VersionConflictError. Updates `application` in place.
    """
    if application.version != expected_version:
        raise VersionConflictError()
    check_transition(application.status, target)

    # Optimistic locking: the WHERE on version makes the check and the write one atomic step.
    # If another request changed the row in the meantime, no row matches and nothing is written.
    updated = LoanApplication.objects.filter(id=application.id, version=expected_version).update(
        status=target, version=F("version") + 1, updated_at=timezone.now(), **(updates or {})
    )
    if updated == 0:
        raise VersionConflictError()

    application.status = target
    application.version = expected_version + 1
    for name, value in (updates or {}).items():
        setattr(application, name, value)
