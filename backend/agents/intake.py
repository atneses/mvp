from countries.base import InvalidDocumentError
from countries.registry import get_plugin

from .base import Agent, AgentContext, AgentResult


class IntakeAgent(Agent):
    name = "intake"
    fields = frozenset({"country", "document"})

    def run(self, context: AgentContext) -> AgentResult:
        # The API already validated it; this catches applications that did not come
        # through the API, or were created before a validator became stricter.
        try:
            get_plugin(context["country"]).validate_document(context["document"])
        except InvalidDocumentError as error:
            return AgentResult(next_status="REJECTED", reason=str(error))
        return AgentResult(next_status="FETCHING_BANK_DATA")
