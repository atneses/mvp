from decimal import Decimal

# Pure and versioned: same inputs, same version, same decision.
VERSION = "MX@1"
MAX_AMOUNT_TO_INCOME = Decimal("12")


def evaluate(amount: Decimal, monthly_income: Decimal, bank_profile: dict) -> tuple[str, str]:
    if amount > monthly_income * MAX_AMOUNT_TO_INCOME:
        return "REJECTED", f"{VERSION}: amount above {MAX_AMOUNT_TO_INCOME}x monthly income"
    return "APPROVED", f"{VERSION}: all rules passed"
