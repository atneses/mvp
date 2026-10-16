from tools.llm import MockLLM

from .base import Agent, AgentContext, AgentResult

WORDING = {
    "APPROVED": "was approved",
    "REJECTED": "was rejected",
    "MANUAL_REVIEW": "needs a manual review",
}


class ExplainerAgent(Agent):
    """Writes a readable summary for the analyst. It never decides anything."""

    name = "explainer"
    # No name or document: nothing personal can reach the LLM.
    fields = frozenset({"country", "status", "amount", "monthly_income"})

    def __init__(self, llm=None):
        self.llm = llm or MockLLM()

    def run(self, context: AgentContext) -> AgentResult:
        prompt = (
            f"The {context['country']} application of {context['amount']} "
            f"with a monthly income of {context['monthly_income']} "
            f"{WORDING[context['status']]} by the country rules."
        )
        return AgentResult(next_status=None, updates={"explanation": self.llm.complete(prompt)})
