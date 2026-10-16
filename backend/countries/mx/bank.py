from decimal import Decimal

from django.conf import settings

from tools.http import post_json


def fetch_bank_profile(document: str) -> dict:
    data = post_json(settings.MX_BANK_URL, {"curp": document})
    # Adapter: the Mexican bank nests its data and sends amounts in cents.
    cents = data["cliente"]["pagos_mensuales_centavos"]
    return {"monthly_debt_payments": str(Decimal(cents) / 100)}
