from django.db import migrations

# Every status change, in the same transaction that makes it:
# a job for the workers, an audit row and two notifications. Either all of it
# is committed or none of it (transactional outbox, no dual write).
STATUS_CHANGE_TRIGGER = """
CREATE FUNCTION loan_application_status_changed() RETURNS trigger AS $$
DECLARE
    -- Set by core.audit.audit_context; empty when the change comes from elsewhere.
    actor text := nullif(current_setting('app.actor_id', true), '');
    correlation text := coalesce(current_setting('app.correlation_id', true), '');
    reason text := nullif(current_setting('app.reason', true), '');
BEGIN
    -- One job per version: replaying the same version inserts nothing.
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
            'reason', reason
        ),
        correlation
    );

    -- Delivered on commit. Ids and status only: channels are not a place for PII.
    PERFORM pg_notify('jobs', 'advance');
    PERFORM pg_notify('application_events', json_build_object(
        'id', NEW.id, 'country', NEW.country, 'status', NEW.status, 'version', NEW.version
    )::text);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER loan_application_created
AFTER INSERT ON loan_applications
FOR EACH ROW EXECUTE FUNCTION loan_application_status_changed();

CREATE TRIGGER loan_application_status_updated
AFTER UPDATE OF status ON loan_applications
FOR EACH ROW WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION loan_application_status_changed();
"""

DROP_STATUS_CHANGE_TRIGGER = """
DROP TRIGGER loan_application_status_updated ON loan_applications;
DROP TRIGGER loan_application_created ON loan_applications;
DROP FUNCTION loan_application_status_changed();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("loans", "0003_auditevent"),
        ("orchestration", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(STATUS_CHANGE_TRIGGER, reverse_sql=DROP_STATUS_CHANGE_TRIGGER),
    ]
