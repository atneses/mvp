from decimal import Decimal

import pytest

from countries.mx.rules import evaluate


@pytest.mark.parametrize(
    ("amount", "decision"),
    [("120000.00", "APPROVED"), ("120000.01", "REJECTED")],
)
def test_amount_above_twelve_monthly_incomes_is_rejected(amount, decision):
    result, reason = evaluate(Decimal(amount), Decimal("10000"), {"monthly_debt_payments": "0"})

    assert result == decision
    assert reason.startswith("MX@1")
