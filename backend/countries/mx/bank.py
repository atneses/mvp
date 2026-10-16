import json
import urllib.request
from decimal import Decimal

from django.conf import settings

TIMEOUT_SECONDS = 5


def fetch_bank_profile(document: str) -> dict:
    request = urllib.request.Request(
        settings.MX_BANK_URL,
        data=json.dumps({"curp": document}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        data = json.load(response)
    # Adapter: the Mexican bank nests its data and sends amounts in cents.
    cents = data["cliente"]["pagos_mensuales_centavos"]
    return {"monthly_debt_payments": str(Decimal(cents) / 100)}
