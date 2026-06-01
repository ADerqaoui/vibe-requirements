"""Gateway adapter selection."""
from app.config import Settings
from app.gateway.anthropic import AnthropicGateway
from app.gateway.base import Gateway, GatewayError
from app.gateway.deepseek import DeepseekGateway
from app.gateway.ollama import OllamaGateway
from app.gateway.openai import OpenAIGateway
from app.models.model import Model

CLOUD_PROVIDERS = {"anthropic", "openai", "deepseek"}


def build_gateway(model: Model, settings: Settings) -> Gateway:
    """Return the adapter for a model provider."""
    if model.provider == "ollama":
        if model.ollama_tag is None:
            raise GatewayError("ollama model is missing ollama_tag")
        return OllamaGateway(settings.ollama_host, model.ollama_tag)
    if model.provider == "anthropic":
        return AnthropicGateway(settings.anthropic_api_key, model.api_model_id)
    if model.provider == "openai":
        return OpenAIGateway(settings.openai_api_key, model.api_model_id)
    if model.provider == "deepseek":
        return DeepseekGateway(settings.deepseek_api_key, model.api_model_id)
    raise GatewayError(f"unknown provider: {model.provider}")
