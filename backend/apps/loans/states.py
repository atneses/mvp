"""State machine: which status changes are allowed.

A common base flow plus the extra transitions each country plugin declares
(e.g. MX waits for an asynchronous bank callback). Manual and automatic
changes go through the same check.
"""

from countries.registry import get_plugin

from .models import LoanApplication

S = LoanApplication.Status

BASE_TRANSITIONS: dict[str, set[str]] = {
    S.CREATED: {S.VALIDATING, S.CANCELLED},
    S.VALIDATING: {S.FETCHING_BANK_DATA, S.REJECTED, S.CANCELLED, S.FAILED},
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


def check_transition(country: str, current: str, target: str) -> None:
    """Raise InvalidTransitionError if `current -> target` is not allowed in `country`."""
    if target not in _transitions(country).get(current, set()):
        raise InvalidTransitionError(f"{current} -> {target} is not allowed for {country}.")


def _transitions(country: str) -> dict[str, set[str]]:
    # Base flow plus the country's extra transitions.
    transitions = {status: set(targets) for status, targets in BASE_TRANSITIONS.items()}
    for status, targets in get_plugin(country).state_extension.items():
        transitions.setdefault(status, set()).update(targets)
    return transitions
