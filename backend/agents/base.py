from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar


class FieldNotAllowedError(LookupError):
    pass


class AgentContext:
    def __init__(self, source: Any, fields: frozenset[str]):
        self._values = {name: getattr(source, name) for name in fields}

    def __getitem__(self, name: str) -> Any:
        if name not in self._values:
            raise FieldNotAllowedError(f"Field {name!r} is not in this agent's policy.")
        return self._values[name]


@dataclass(frozen=True)
class AgentResult:
    next_status: str


class Agent(ABC):
    name: ClassVar[str]
    fields: ClassVar[frozenset[str]]

    @abstractmethod
    def run(self, context: AgentContext) -> AgentResult: ...
