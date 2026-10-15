"""Correlation id: one id per request, present in every log line and in the response."""

import re
import time
import uuid

import structlog

HEADER = "X-Correlation-ID"
# Only accept short, safe ids from clients (avoids log injection).
VALID_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")

logger = structlog.get_logger("request")


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get(HEADER, "")
        correlation_id = incoming if VALID_ID.match(incoming) else str(uuid.uuid4())

        # Context vars are added to every log line emitted while handling this request.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        request.correlation_id = correlation_id

        start = time.perf_counter()
        response = self.get_response(request)

        logger.info(
            "request_finished",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - start) * 1000, 1),
        )
        response[HEADER] = correlation_id
        return response
