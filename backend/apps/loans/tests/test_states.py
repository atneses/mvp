import pytest

from apps.loans.models import LoanApplication
from apps.loans.states import InvalidTransitionError, check_transition

S = LoanApplication.Status


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (S.CREATED, S.APPROVED),  # skipping the whole flow
        (S.APPROVED, S.CREATED),  # leaving a final state
        (S.REJECTED, S.EVALUATING),
    ],
)
def test_illegal_transitions_are_rejected(current, target):
    with pytest.raises(InvalidTransitionError):
        check_transition("ES", current, target)


@pytest.mark.parametrize(("country", "allowed"), [("MX", True), ("ES", False)])
def test_only_mexico_waits_for_the_bank_callback(country, allowed):
    try:
        check_transition(country, S.FETCHING_BANK_DATA, S.WAITING_BANK_CALLBACK)
        result = True
    except InvalidTransitionError:
        result = False

    assert result is allowed
