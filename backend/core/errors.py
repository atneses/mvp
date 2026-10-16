"""One error format for the whole API, so the frontend can show any error the same way:

{"code": "...", "message": "...", "details": {...} | null, "correlation_id": "..."}
"""

import structlog
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = structlog.get_logger("errors")


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    correlation_id = getattr(context["request"], "correlation_id", None)

    if response is None:
        # Unexpected error: log it with its traceback, never send internals to the client.
        logger.exception("unhandled_error")
        return Response(
            _body("server_error", "Internal server error.", None, correlation_id),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, exceptions.ValidationError):
        # Field errors go in details, e.g. {"document": ["Invalid control letter."]}.
        body = _body("validation_error", "Invalid input.", response.data, correlation_id)
    elif isinstance(exc, Http404):
        # Generic message: Django's one names the model ("No LoanApplication matches...").
        body = _body("not_found", "Not found.", None, correlation_id)
    else:
        detail = response.data.get("detail", "")
        # SimpleJWT puts its own code next to the detail ("token_not_valid").
        code = response.data.get("code") or getattr(detail, "code", None) or "error"
        body = _body(str(code), str(detail), None, correlation_id)

    response.data = body
    return response


def _body(code, message, details, correlation_id):
    return {"code": code, "message": message, "details": details, "correlation_id": correlation_id}
