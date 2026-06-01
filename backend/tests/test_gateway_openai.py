"""OpenAI gateway adapter tests."""
import pytest

from app.gateway.openai import OpenAIGateway
from gateway_cloud_helpers import assert_malformed_response
from gateway_cloud_helpers import assert_missing_configuration
from gateway_cloud_helpers import assert_network_failure
from gateway_cloud_helpers import assert_status_error
from gateway_cloud_helpers import assert_success_request
from gateway_cloud_helpers import openai_success


@pytest.mark.asyncio
async def test_openai_adapter_parses_success_and_sends_expected_request() -> None:
    """OpenAI responses map into the gateway contract."""
    await assert_success_request(
        gateway_class=OpenAIGateway,
        path="/v1/chat/completions",
        response_body=openai_success("openai ok"),
        expected_text="openai ok",
        expected_in_tokens=13,
        expected_out_tokens=5,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "message", "retryable"),
    [
        (401, "authentication failed", False),
        (403, "authentication failed", False),
        (429, "rate limited", True),
        (503, "provider unavailable", True),
    ],
)
async def test_openai_adapter_maps_status_errors(
    status_code: int,
    message: str,
    retryable: bool,
) -> None:
    """OpenAI status errors are mapped clearly."""
    await assert_status_error(OpenAIGateway, "openai", status_code, message, retryable)


@pytest.mark.asyncio
async def test_openai_adapter_rejects_malformed_response() -> None:
    """Malformed OpenAI payloads become GatewayError values."""
    await assert_malformed_response(OpenAIGateway, "openai", {"choices": [], "usage": {}})


@pytest.mark.asyncio
async def test_openai_adapter_maps_network_failure() -> None:
    """OpenAI network failures stay retryable."""
    await assert_network_failure(OpenAIGateway, "openai")


def test_openai_adapter_missing_api_key_fails_before_http() -> None:
    """Missing OpenAI API key fails during construction."""
    assert_missing_configuration(
        OpenAIGateway,
        "openai",
        lambda: OpenAIGateway("", "gpt-test", None),
        "API key is not configured",
    )


def test_openai_adapter_missing_model_id_fails_before_http() -> None:
    """Missing OpenAI model id fails during construction."""
    assert_missing_configuration(
        OpenAIGateway,
        "openai",
        lambda: OpenAIGateway("secret", None, None),
        "model is missing api_model_id",
    )
