from decimal import Decimal

import pytest

from countries.es.rules import evaluate


@pytest.mark.parametrize(
    ("amount", "decision"),
    [("20000.00", "APPROVED"), ("20000.01", "MANUAL_REVIEW")],
)
def test_amount_above_the_threshold_needs_manual_review(amount, decision):
    result, reason = evaluate(Decimal(amount), Decimal("3000"), {"monthly_debt_payments": "0"})

    assert result == decision
    assert reason.startswith("ES@1")
