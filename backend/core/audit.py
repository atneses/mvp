"""Pass who/why to the database triggers, which cannot see the HTTP request."""

from contextlib import contextmanager

from django.db import connection, transaction


@contextmanager
def audit_context(*, actor_id=None, correlation_id="", reason="", agent=""):
    """Open a transaction whose changes the triggers attribute to this actor and request.

    set_config(..., true) is local to the transaction: nothing leaks to the next one.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.actor_id', %s, true),"
                " set_config('app.correlation_id', %s, true),"
                " set_config('app.reason', %s, true),"
                " set_config('app.agent', %s, true)",
                [str(actor_id or ""), correlation_id or "", reason or "", agent or ""],
            )
        yield
