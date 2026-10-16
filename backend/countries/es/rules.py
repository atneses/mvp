from decimal import Decimal

# Pure and versioned: same inputs, same version, same decision.
VERSION = "ES@1"
MANUAL_REVIEW_ABOVE = Decimal("20000")


def evaluate(amount: Decimal, monthly_income: Decimal, bank_profile: dict) -> tuple[str, str]:
    if amount > MANUAL_REVIEW_ABOVE:
        return "MANUAL_REVIEW", f"{VERSION}: amount above {MANUAL_REVIEW_ABOVE} EUR"
    return "APPROVED", f"{VERSION}: all rules passed"
