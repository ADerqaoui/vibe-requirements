"""Anthropic gateway adapter tests."""
import pytest

from app.gateway.anthropic import AnthropicGateway
from gateway_cloud_helpers import assert_invalid_json_response
from gateway_cloud_helpers import assert_malformed_response
from gateway_cloud_helpers import assert_missing_configuration
from gateway_cloud_helpers import assert_network_failure
from gateway_cloud_helpers import assert_status_error
from gateway_cloud_helpers import assert_success_request


def anthropic_success() -> dict[str, object]:
    """Return an Anthropic-style success payload."""
    return {
        "content": [{"type": "text", "text": "anthropic ok"}],
        "usage": {"input_tokens": 11, "output_tokens": 7},
    }


@pytest.mark.asyncio
async def test_anthropic_adapter_parses_success_and_sends_expected_request() -> None:
    """Anthropic responses map into the gateway contract."""
    await assert_success_request(
        gateway_class=AnthropicGateway,
        path="/v1/messages",
        response_body=anthropic_success(),
        expected_text="anthropic ok",
        expected_in_tokens=11,
        expected_out_tokens=7,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "message", "retryable"),
    [
        (401, "authentication failed", False),
        (403, "authentication failed", False),
        (429, "rate limited", True),
        (500, "provider unavailable", True),
    ],
)
async def test_anthropic_adapter_maps_status_errors(
    status_code: int,
    message: str,
    retryable: bool,
) -> None:
    """Anthropic status errors are mapped clearly."""
    await assert_status_error(AnthropicGateway, "anthropic", status_code, message, retryable)


@pytest.mark.asyncio
async def test_anthropic_adapter_rejects_malformed_response() -> None:
    """Malformed Anthropic payloads become GatewayError values."""
    await assert_malformed_response(AnthropicGateway, "anthropic", {"content": [], "usage": {}})


@pytest.mark.asyncio
async def test_anthropic_adapter_rejects_invalid_json_response() -> None:
    """Invalid JSON Anthropic payloads become non-retryable malformed responses."""
    await assert_invalid_json_response(AnthropicGateway, "anthropic")


@pytest.mark.asyncio
async def test_anthropic_adapter_maps_network_failure() -> None:
    """Anthropic network failures stay retryable."""
    await assert_network_failure(AnthropicGateway, "anthropic")


def test_anthropic_adapter_missing_api_key_fails_before_http() -> None:
    """Missing Anthropic API key fails during construction."""
    assert_missing_configuration(
        AnthropicGateway,
        "anthropic",
        lambda: AnthropicGateway("", "claude-test", None),
        "API key is not configured",
    )


def test_anthropic_adapter_missing_model_id_fails_before_http() -> None:
    """Missing Anthropic model id fails during construction."""
    assert_missing_configuration(
        AnthropicGateway,
        "anthropic",
        lambda: AnthropicGateway("secret", None, None),
        "model is missing api_model_id",
    )
