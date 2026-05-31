"""Gateway factory tests."""
import pytest

from app.config import Settings
from app.gateway.base import GatewayError
from app.gateway.factory import build_gateway
from app.models.model import Model


@pytest.mark.asyncio
async def test_cloud_provider_adapter_is_not_implemented() -> None:
    """Cloud providers raise the explicit slice-05 placeholder error."""
    model = Model(provider="openai", name="gpt", api_model_id="gpt-test", tier="high")
    gateway = build_gateway(model, Settings())

    with pytest.raises(GatewayError, match="adapter not implemented"):
        await gateway.health_check(1)
