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
        check_transition(current, target)
