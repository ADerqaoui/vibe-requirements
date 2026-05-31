"""Retry and timeout handling for gateway calls."""
from app.gateway.base import Gateway, GatewayError, GatewayResult


async def complete_with_retries(
    gateway: Gateway,
    prompt: str,
    system: str | None,
    retry_count: int,
    timeout_seconds: float,
) -> GatewayResult:
    """Health-check and complete, retrying the same model on clean gateway failures."""
    attempts = max(0, retry_count) + 1
    last_error: GatewayError | None = None
    for _attempt in range(attempts):
        try:
            await gateway.health_check(timeout_seconds)
            return await gateway.complete(prompt, system, timeout_seconds)
        except GatewayError as error:
            last_error = error
    if last_error is None:
        raise GatewayError("gateway call failed")
    raise GatewayError(str(last_error)) from last_error


class SequencedGateway:
    """Test helper-style gateway that consumes injected call outcomes."""

    def __init__(self, outcomes: list[GatewayResult | GatewayError]):
        self._outcomes = list(outcomes)
        self.health_checks = 0
        self.calls = 0

    async def health_check(self, timeout_seconds: float) -> None:
        """Count health checks."""
        self.health_checks += 1

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Return or raise the next injected outcome."""
        self.calls += 1
        if not self._outcomes:
            raise GatewayError("no gateway outcome configured")
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, GatewayError):
            raise outcome
        return outcome
