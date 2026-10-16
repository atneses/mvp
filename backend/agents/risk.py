from countries.registry import get_plugin

from .base import Agent, AgentContext, AgentResult


class RiskAgent(Agent):
    name = "risk"
    # No name or document: the decision does not depend on who the applicant is.
    fields = frozenset({"country", "amount", "monthly_income", "bank_profile"})

    def run(self, context: AgentContext) -> AgentResult:
        decision, reason = get_plugin(context["country"]).evaluate(
            context["amount"], context["monthly_income"], context["bank_profile"]
        )
        return AgentResult(next_status=decision, reason=reason)
