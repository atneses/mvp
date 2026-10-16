import structlog

from agents.banking import BankingAgent
from agents.base import AgentContext
from agents.explainer import ExplainerAgent
from agents.intake import IntakeAgent
from agents.risk import RiskAgent
from apps.loans.models import LoanApplication
from apps.loans.services import VersionConflictError, change_status, save_updates
from core.audit import audit_context

from .models import Job

S = LoanApplication.Status

AGENTS = {
    S.CREATED: IntakeAgent(),
    S.FETCHING_BANK_DATA: BankingAgent(),
    S.EVALUATING: RiskAgent(),
    S.APPROVED: ExplainerAgent(),
    S.REJECTED: ExplainerAgent(),
    S.MANUAL_REVIEW: ExplainerAgent(),
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
    agent = AGENTS.get(application.status)
    if agent is None:
        return

    result = agent.run(AgentContext(application, agent.fields))
    if result.next_status is None:
        try:
            save_updates(application, application.version, result.updates)
        except VersionConflictError:
            logger.info("version_conflict_skipped", agent=agent.name)
        return
    try:
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
