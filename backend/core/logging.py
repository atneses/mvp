"""Structured JSON logging with structlog.

Every log line (ours, Django's and third-party libraries') goes through the same
pipeline: add context (correlation_id, level, timestamp, service), redact PII and
render one JSON object per line.
"""

import re

import structlog

REDACTED = "[REDACTED]"

# Keys whose value is always PII, whatever it contains.
SENSITIVE_KEYS = frozenset(
    {
        "document",
        "dni",
        "nie",
        "curp",
        "full_name",
        "iban",
        "password",
        "token",
        "access",
        "refresh",
        "authorization",
    }
)

# Identity documents that may slip into free text (e.g. an error message).
PII_PATTERNS = (
    re.compile(r"\b\d{8}[A-Z]\b"),  # DNI (ES)
    re.compile(r"\b[XYZ]\d{7}[A-Z]\b"),  # NIE (ES)
    re.compile(r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b"),  # CURP (MX)
)


def configure_logging(service: str, level: str) -> dict:
    """Configure structlog and return the dict for Django's LOGGING setting."""
    shared = _shared_processors(service)

    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": shared,
                # Redaction is the last step before rendering, so it covers every line.
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    redact_pii,
                    structlog.processors.JSONRenderer(),
                ],
            },
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "json"},
        },
        "root": {"handlers": ["console"], "level": level},
        # Drop Django's default plain-text handler; its records reach root and go out as JSON.
        "loggers": {"django": {"handlers": [], "level": level, "propagate": True}},
    }


def redact_pii(logger, method_name, event_dict):
    """structlog processor: hide sensitive keys and document numbers."""
    return _redact_value(event_dict)


def _shared_processors(service: str) -> list:
    # Run on every event, both structlog's and stdlib's (Django, psycopg...).
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
        _add_service(service),
        structlog.processors.format_exc_info,
    ]


def _add_service(service: str):
    def processor(logger, method_name, event_dict):
        event_dict["service"] = service
        return event_dict

    return processor


def _redact_value(value):
    if isinstance(value, str):
        for pattern in PII_PATTERNS:
            value = pattern.sub(REDACTED, value)
        return value
    if isinstance(value, dict):
        return {
            k: REDACTED if str(k).lower() in SENSITIVE_KEYS else _redact_value(v)
            for k, v in value.items()
        }
    if isinstance(value, list | tuple):
        return [_redact_value(v) for v in value]
    return value
