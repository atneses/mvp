"""LLM tool. Simulated, so the project runs without external credentials."""


class MockLLM:
    def complete(self, prompt: str) -> str:
        # Deterministic: the same prompt always gives the same text.
        return f"[simulated LLM] {prompt}"
