import structlog

from agents.banking import BankingAgent
from agents.base import AgentContext
from agents.explainer import ExplainerAgent
from agents.intake import IntakeAgent
from agents.notifier import NotifierAgent
from agents.risk import RiskAgent
from apps.loans.models import LoanApplication
from apps.loans.services import VersionConflictError, change_status, save_updates
from apps.loans.states import InvalidTransitionError
from core.audit import audit_context

from .models import Job

S = LoanApplication.Status

# Agents run in order; the first one that changes the status ends the step.
AGENTS = {
    S.CREATED: [IntakeAgent()],
    S.FETCHING_BANK_DATA: [BankingAgent()],
    S.EVALUATING: [RiskAgent()],
    S.APPROVED: [ExplainerAgent(), NotifierAgent()],
    S.REJECTED: [ExplainerAgent(), NotifierAgent()],
    S.MANUAL_REVIEW: [ExplainerAgent(), NotifierAgent()],
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
    for agent in AGENTS.get(application.status, []):
        try:
            if not _run(agent, application, job):
                return
        except Exception as error:
            if job.attempts >= job.max_attempts:
                _mark_failed(application, job, agent, error)
            raise  # the queue retries it, or marks it dead after the last attempt


def _run(agent, application, job) -> bool:
    """Run one agent and save its result. Returns False when the step is over."""
    result = agent.run(AgentContext(application, agent.fields))
    try:
        if result.next_status is None:
            if result.updates:
                save_updates(application, application.version, result.updates)
            return True
        with audit_context(
            correlation_id=job.correlation_id, reason=result.reason, agent=agent.name
        ):
            change_status(
                application,
                result.next_status,
                expected_version=application.version,
                updates=result.updates,
            )
    except VersionConflictError:
        logger.info("version_conflict_skipped", agent=agent.name)
    return False


def _mark_failed(application, job, agent, error):
    try:
        with audit_context(correlation_id=job.correlation_id, reason=repr(error), agent=agent.name):
            change_status(application, S.FAILED, expected_version=application.version)
    except InvalidTransitionError, VersionConflictError:
        # Already decided (e.g. only the notification failed) or changed meanwhile: keep it.
        logger.info("failed_status_skipped", status=application.status)
