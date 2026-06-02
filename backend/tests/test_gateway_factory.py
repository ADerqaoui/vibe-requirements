"""Gateway factory tests."""
import pytest

from app.config import Settings
from app.gateway.base import GatewayError
from app.gateway.anthropic import AnthropicGateway
from app.gateway.deepseek import DeepseekGateway
from app.gateway.factory import build_gateway
from app.gateway.ollama import OllamaGateway
from app.gateway.openai import OpenAIGateway
from app.models.model import Model


def test_factory_routes_ollama_provider() -> None:
    """Ollama models build the local adapter."""
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid")

    gateway = build_gateway(model, Settings())

    assert isinstance(gateway, OllamaGateway)


@pytest.mark.parametrize(
    ("provider", "api_key_name", "gateway_class"),
    [
        ("anthropic", "anthropic_api_key", AnthropicGateway),
        ("openai", "openai_api_key", OpenAIGateway),
        ("deepseek", "deepseek_api_key", DeepseekGateway),
    ],
)
def test_factory_routes_cloud_providers(
    provider: str,
    api_key_name: str,
    gateway_class: type,
) -> None:
    """Cloud models build their concrete provider adapters."""
    model = Model(provider=provider, name=provider, api_model_id=f"{provider}-model", tier="high")
    settings = Settings(**{api_key_name: "secret"})

    gateway = build_gateway(model, settings)

    assert isinstance(gateway, gateway_class)


def test_factory_rejects_unknown_provider() -> None:
    """Unknown providers fail clearly."""
    model = Model(provider="other", name="other", tier="low")

    with pytest.raises(GatewayError, match="unknown provider: other"):
        build_gateway(model, Settings())
