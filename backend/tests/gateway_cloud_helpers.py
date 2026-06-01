"""Shared helpers for cloud gateway adapter tests."""
from collections.abc import Callable

import httpx
import pytest

from app.gateway.base import GatewayError


def openai_success(text: str) -> dict[str, object]:
    """Return an OpenAI-compatible success payload."""
    return {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": 13, "completion_tokens": 5},
    }


async def assert_success_request(
    gateway_class: type,
    path: str,
    response_body: dict[str, object],
    expected_text: str,
    expected_in_tokens: int,
    expected_out_tokens: int,
) -> None:
    """Assert a cloud adapter parses success and sends expected request data."""
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == path
        assert request.method == "POST"
        return httpx.Response(200, json=response_body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = gateway_class("secret", "provider-model", client)

    await gateway.health_check(1)
    result = await gateway.complete("hello", "system", 3)
    await client.aclose()

    sent_body = requests[0].read().decode()
    assert result.text == expected_text
    assert result.in_tokens == expected_in_tokens
    assert result.out_tokens == expected_out_tokens
    assert "provider-model" in sent_body
    assert "hello" in sent_body
    assert "system" in sent_body


async def assert_status_error(
    gateway_class: type,
    provider: str,
    status_code: int,
    message: str,
    retryable: bool,
) -> None:
    """Assert HTTP status errors map to clear GatewayError values."""

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "bad"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = gateway_class("secret", "provider-model", client)

    with pytest.raises(GatewayError, match=message) as raised:
        await gateway.complete("hello", None, 1)
    await client.aclose()

    assert provider in str(raised.value)
    assert raised.value.retryable is retryable


async def assert_malformed_response(
    gateway_class: type,
    provider: str,
    response_body: dict[str, object],
) -> None:
    """Assert malformed payloads become non-retryable GatewayError values."""

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = gateway_class("secret", "provider-model", client)

    with pytest.raises(GatewayError, match=f"{provider} malformed response") as raised:
        await gateway.complete("hello", None, 1)
    await client.aclose()

    assert raised.value.retryable is False


async def assert_network_failure(gateway_class: type, provider: str) -> None:
    """Assert network failures stay retryable GatewayError values."""

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = gateway_class("secret", "provider-model", client)

    with pytest.raises(GatewayError, match=f"{provider} request failed") as raised:
        await gateway.complete("hello", None, 1)
    await client.aclose()

    assert raised.value.retryable is True


def assert_missing_configuration(
    gateway_class: type,
    provider: str,
    constructor: Callable[[], object],
    message: str,
) -> None:
    """Assert constructor-time configuration failures are non-retryable."""
    with pytest.raises(GatewayError, match=f"{provider} {message}") as raised:
        constructor()

    assert raised.value.retryable is False
