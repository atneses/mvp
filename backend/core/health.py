"""Health endpoints for Docker and Kubernetes.

- /healthz: the process is alive (liveness). Does not touch external dependencies.
- /readyz: the process can serve traffic (readiness). Checks Postgres and Redis.
"""

import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    return JsonResponse({"status": "ok"})


def readyz(request):
    checks = {
        "database": _database_is_ready(),
        "redis": _redis_is_ready(),
    }
    ready = all(checks.values())
    return JsonResponse(
        {"status": "ok" if ready else "unavailable", "checks": checks},
        status=200 if ready else 503,
    )


def _database_is_ready() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        # A broken connection must not be reused by the next request.
        connection.close()
        return False


def _redis_is_ready() -> bool:
    try:
        client = redis.Redis.from_url(
            settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2
        )
        client.ping()
        return True
    except redis.RedisError:
        return False
