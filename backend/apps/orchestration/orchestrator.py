import time

import structlog

from agents.base import AgentContext
from agents.stubs import PassThroughAgent
from apps.loans.models import LoanApplication
from apps.loans.services import VersionConflictError, change_status
from core.audit import audit_context

from .models import AgentRun, Job

S = LoanApplication.Status

AGENTS = {
    S.VALIDATING: PassThroughAgent("intake", S.FETCHING_BANK_DATA),
    S.FETCHING_BANK_DATA: PassThroughAgent("banking", S.EVALUATING),
    S.EVALUATING: PassThroughAgent("risk", S.APPROVED),
}

logger = structlog.get_logger("orchestrator")


def advance(job: Job) -> None:
    """Run the agent of the application's current status and move it to the next one."""
    application = LoanApplication.objects.get(id=job.application_id)
    # Each job is for one version ("<id>:<version>"); if the application changed since,
    # a newer job exists and this one is stale.
    if application.version != int(job.dedupe_key.rsplit(":", 1)[1]):
        logger.info("stale_job_skipped", version=application.version)
        return

    if application.status == S.CREATED:
        _move(application, S.VALIDATING, job)
        return
    agent = AGENTS.get(application.status)
    if agent is None:
        return

    started = time.monotonic()
    try:
        result = agent.run(AgentContext(application, agent.fields))
    except Exception as error:
        AgentRun.objects.create(**_run(job, agent, started, "failed", error=repr(error)))
        raise
    output = {"next_status": result.next_status}
    _move(application, result.next_status, job, _run(job, agent, started, "succeeded", output))


def _move(application, target, job, agent_run=None):
    try:
        # One transaction: the agent trace and the status change are saved together or not at all.
        with audit_context(correlation_id=job.correlation_id):
            if agent_run:
                AgentRun.objects.create(**agent_run)
            change_status(application, target, expected_version=application.version)
    except VersionConflictError:
        logger.info("version_conflict_skipped", target=target)


def _run(job, agent, started, status, output=None, error=""):
    return {
        "application_id": job.application_id,
        "job_id": job.id,
        "agent": agent.name,
        "status": status,
        "output": output or {},
        "duration_ms": int((time.monotonic() - started) * 1000),
        "error": error,
        "correlation_id": job.correlation_id,
    }
