"""Provider-agnostic LLM gateway contracts."""
from dataclasses import dataclass
from typing import Protocol


class GatewayError(Exception):
    """Raised when a gateway call cannot complete cleanly."""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class CostCeilingExceededError(GatewayError):
    """Raised before a paid call when monthly spend has reached the ceiling."""

    def __init__(self, spent_sek: float, ceiling_sek: float):
        super().__init__("cost ceiling exceeded", retryable=False)
        self.spent_sek = spent_sek
        self.ceiling_sek = ceiling_sek


@dataclass(frozen=True)
class GatewayResult:
    """Normalized LLM completion result."""

    text: str
    in_tokens: int
    out_tokens: int


class Gateway(Protocol):
    """Provider adapter contract."""

    async def health_check(self, timeout_seconds: float) -> None:
        """Raise GatewayError if the provider is not ready."""

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Send a completion request and return normalized usage."""
