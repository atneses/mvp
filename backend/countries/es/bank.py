import json
import urllib.request

from django.conf import settings

TIMEOUT_SECONDS = 5


def fetch_bank_profile(document: str) -> dict:
    request = urllib.request.Request(
        settings.ES_BANK_URL,
        data=json.dumps({"dni": document}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        data = json.load(response)
    # Adapter: the Spanish bank's own field names, translated to the common profile.
    return {"monthly_debt_payments": data["cuota_mensual_deudas"]}
