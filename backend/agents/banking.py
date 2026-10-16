from countries.registry import get_plugin

from .base import Agent, AgentContext, AgentResult


class BankingAgent(Agent):
    name = "banking"
    fields = frozenset({"country", "document"})

    def run(self, context: AgentContext) -> AgentResult:
        profile = get_plugin(context["country"]).fetch_bank_profile(context["document"])
        return AgentResult(next_status="EVALUATING", updates={"bank_profile": profile})
