from .base import Agent, AgentContext, AgentResult


class PassThroughAgent(Agent):
    """Placeholder until the real agent exists: sees nothing and moves on."""

    fields = frozenset()

    def __init__(self, name: str, next_status: str):
        self.name = name
        self.next_status = next_status

    def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(next_status=self.next_status)
