"""Gateway resilience tests."""
import pytest

from app.gateway.base import GatewayError, GatewayResult
from app.gateway.resilience import complete_with_retries


class FlakyGateway:
    """Fake gateway with independently controlled health and completion failures."""

    def __init__(self, health_failures: int, completion_failures: int):
        self.health_failures = health_failures
        self.completion_failures = completion_failures
        self.health_checks = 0
        self.calls = 0
        self.timeouts: list[float] = []

    async def health_check(self, timeout_seconds: float) -> None:
        self.health_checks += 1
        self.timeouts.append(timeout_seconds)
        if self.health_checks <= self.health_failures:
            raise GatewayError("health unavailable")

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        self.calls += 1
        self.timeouts.append(timeout_seconds)
        if self.calls <= self.completion_failures:
            raise GatewayError("timeout")
        return GatewayResult(text="ok", in_tokens=1, out_tokens=2)


@pytest.mark.asyncio
async def test_resilience_retries_then_succeeds() -> None:
    """Completion failures retry the same gateway."""
    gateway = FlakyGateway(health_failures=0, completion_failures=1)

    result = await complete_with_retries(gateway, "prompt", None, retry_count=2, timeout_seconds=9)

    assert result.text == "ok"
    assert gateway.health_checks == 2
    assert gateway.calls == 2
    assert gateway.timeouts == [9, 9, 9, 9]


@pytest.mark.asyncio
async def test_resilience_raises_after_retry_count() -> None:
    """Failures stop after initial attempt plus retry_count."""
    gateway = FlakyGateway(health_failures=0, completion_failures=3)

    with pytest.raises(GatewayError, match="timeout"):
        await complete_with_retries(gateway, "prompt", None, retry_count=2, timeout_seconds=5)

    assert gateway.health_checks == 3
    assert gateway.calls == 3


@pytest.mark.asyncio
async def test_health_check_failure_retries() -> None:
    """Health check failures consume retry attempts."""
    gateway = FlakyGateway(health_failures=1, completion_failures=0)

    result = await complete_with_retries(gateway, "prompt", None, retry_count=2, timeout_seconds=4)

    assert result.text == "ok"
    assert gateway.health_checks == 2
    assert gateway.calls == 1


@pytest.mark.asyncio
async def test_timeout_path_is_clean_gateway_error() -> None:
    """Timeout-like adapter errors remain GatewayError after retries."""
    gateway = FlakyGateway(health_failures=0, completion_failures=2)

    with pytest.raises(GatewayError, match="timeout"):
        await complete_with_retries(gateway, "prompt", None, retry_count=1, timeout_seconds=1)
