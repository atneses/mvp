from django.conf import settings

from tools.http import post_json


def fetch_bank_profile(document: str) -> dict:
    data = post_json(settings.ES_BANK_URL, {"dni": document})
    # Adapter: the Spanish bank's own field names, translated to the common profile.
    return {"monthly_debt_payments": data["cuota_mensual_deudas"]}
