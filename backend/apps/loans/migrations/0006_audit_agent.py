from django.db import migrations

# Same function as 0004, now also recording which agent made the change (app.agent).
STATUS_CHANGED_WITH_AGENT = """
CREATE OR REPLACE FUNCTION loan_application_status_changed() RETURNS trigger AS $$
DECLARE
    actor text := nullif(current_setting('app.actor_id', true), '');
    correlation text := coalesce(current_setting('app.correlation_id', true), '');
    reason text := nullif(current_setting('app.reason', true), '');
    agent text := nullif(current_setting('app.agent', true), '');
BEGIN
    INSERT INTO jobs (kind, application_id, dedupe_key, correlation_id)
    VALUES ('advance', NEW.id, NEW.id::text || ':' || NEW.version, correlation)
    ON CONFLICT (dedupe_key) DO NOTHING;

    INSERT INTO audit_events (event, application_id, actor_id, data, correlation_id)
    VALUES (
        'status_changed', NEW.id, actor::bigint,
        jsonb_build_object(
            'from', CASE WHEN TG_OP = 'UPDATE' THEN OLD.status END,
            'to', NEW.status,
            'version', NEW.version,
            'reason', reason,
            'agent', agent
        ),
        correlation
    );

    PERFORM pg_notify('jobs', 'advance');
    PERFORM pg_notify('application_events', json_build_object(
        'id', NEW.id, 'country', NEW.country, 'status', NEW.status, 'version', NEW.version
    )::text);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("loans", "0005_alter_loanapplication_status"),
    ]

    operations = [
        # No reverse: the new function also works with the older schema.
        migrations.RunSQL(STATUS_CHANGED_WITH_AGENT, reverse_sql=migrations.RunSQL.noop),
    ]
