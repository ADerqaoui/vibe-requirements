"""Deepseek gateway adapter tests."""
import pytest

from app.gateway.deepseek import DeepseekGateway
from gateway_cloud_helpers import assert_invalid_json_response
from gateway_cloud_helpers import assert_malformed_response
from gateway_cloud_helpers import assert_missing_configuration
from gateway_cloud_helpers import assert_network_failure
from gateway_cloud_helpers import assert_status_error
from gateway_cloud_helpers import assert_success_request
from gateway_cloud_helpers import openai_success


@pytest.mark.asyncio
async def test_deepseek_adapter_parses_success_and_sends_expected_request() -> None:
    """Deepseek responses map into the gateway contract."""
    await assert_success_request(
        gateway_class=DeepseekGateway,
        path="/v1/chat/completions",
        response_body=openai_success("deepseek ok"),
        expected_text="deepseek ok",
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
        (502, "provider unavailable", True),
    ],
)
async def test_deepseek_adapter_maps_status_errors(
    status_code: int,
    message: str,
    retryable: bool,
) -> None:
    """Deepseek status errors are mapped clearly."""
    await assert_status_error(DeepseekGateway, "deepseek", status_code, message, retryable)


@pytest.mark.asyncio
async def test_deepseek_adapter_rejects_malformed_response() -> None:
    """Malformed Deepseek payloads become GatewayError values."""
    await assert_malformed_response(DeepseekGateway, "deepseek", {"choices": [], "usage": {}})


@pytest.mark.asyncio
async def test_deepseek_adapter_rejects_invalid_json_response() -> None:
    """Invalid JSON Deepseek payloads become non-retryable malformed responses."""
    await assert_invalid_json_response(DeepseekGateway, "deepseek")


@pytest.mark.asyncio
async def test_deepseek_adapter_maps_network_failure() -> None:
    """Deepseek network failures stay retryable."""
    await assert_network_failure(DeepseekGateway, "deepseek")


def test_deepseek_adapter_missing_api_key_fails_before_http() -> None:
    """Missing Deepseek API key fails during construction."""
    assert_missing_configuration(
        DeepseekGateway,
        "deepseek",
        lambda: DeepseekGateway("", "deepseek-test", None),
        "API key is not configured",
    )


def test_deepseek_adapter_missing_model_id_fails_before_http() -> None:
    """Missing Deepseek model id fails during construction."""
    assert_missing_configuration(
        DeepseekGateway,
        "deepseek",
        lambda: DeepseekGateway("secret", None, None),
        "model is missing api_model_id",
    )
