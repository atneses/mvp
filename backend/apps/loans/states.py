"""State machine: which status changes are allowed. Manual and automatic changes share it."""

from .models import LoanApplication

S = LoanApplication.Status

BASE_TRANSITIONS: dict[str, set[str]] = {
    S.CREATED: {S.FETCHING_BANK_DATA, S.REJECTED, S.CANCELLED, S.FAILED},
    S.FETCHING_BANK_DATA: {S.EVALUATING, S.FAILED},
    S.EVALUATING: {S.APPROVED, S.REJECTED, S.MANUAL_REVIEW, S.FAILED},
    S.MANUAL_REVIEW: {S.APPROVED, S.REJECTED, S.EVALUATING, S.CANCELLED},
    # An admin can restart a failed application from the beginning.
    S.FAILED: {S.CREATED},
    # Final states: no way out.
    S.APPROVED: set(),
    S.REJECTED: set(),
    S.CANCELLED: set(),
}


class InvalidTransitionError(Exception):
    pass


def check_transition(current: str, target: str) -> None:
    """Raise InvalidTransitionError if `current -> target` is not allowed."""
    if target not in BASE_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(f"{current} -> {target} is not allowed.")
