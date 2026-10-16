"""Fake bank providers, so the flow runs without real credentials. Dev only."""

import hashlib
import json
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def spain_bank_profile(request):
    dni = json.loads(request.body)["dni"]
    # Same document, same answer: tests and demos are repeatable.
    seed = int(hashlib.sha256(dni.encode()).hexdigest(), 16)
    monthly_debt = Decimal(seed % 150_000) / 100  # 0.00 - 1,499.99 EUR
    return JsonResponse({"cuota_mensual_deudas": str(monthly_debt), "moneda": "EUR"})
