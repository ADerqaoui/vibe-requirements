"""Gateway adapter selection."""
from app.config import Settings
from app.gateway.base import Gateway, GatewayError, GatewayResult
from app.gateway.ollama import OllamaGateway
from app.models.model import Model

CLOUD_PROVIDERS = {"anthropic", "openai", "deepseek"}


class NotImplementedGateway:
    """Placeholder for cloud adapters planned in later slices."""

    async def health_check(self, timeout_seconds: float) -> None:
        """Cloud providers are intentionally not callable in this slice."""
        raise GatewayError("adapter not implemented")

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Cloud providers are intentionally not callable in this slice."""
        raise GatewayError("adapter not implemented")


def build_gateway(model: Model, settings: Settings) -> Gateway:
    """Return the adapter for a model provider."""
    if model.provider == "ollama":
        if model.ollama_tag is None:
            raise GatewayError("ollama model is missing ollama_tag")
        return OllamaGateway(settings.ollama_host, model.ollama_tag)
    if model.provider in CLOUD_PROVIDERS:
        return NotImplementedGateway()
    raise GatewayError(f"unknown provider: {model.provider}")
