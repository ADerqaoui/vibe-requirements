"""Shared HTTP helpers for cloud gateway adapters."""
import json

import httpx

from app.gateway.base import GatewayError

DEFAULT_MAX_TOKENS = 1024


def require_api_model_id(api_model_id: str | None, provider: str) -> str:
    """Return a configured API model id or fail clearly."""
    if api_model_id is None or api_model_id.strip() == "":
        raise GatewayError(f"{provider} model is missing api_model_id", retryable=False)
    return api_model_id


def require_api_key(api_key: str, provider: str) -> str:
    """Return a configured API key or fail before any HTTP call."""
    if api_key.strip() == "":
        raise GatewayError(f"{provider} API key is not configured", retryable=False)
    return api_key


def map_status_error(provider: str, status_code: int) -> GatewayError:
    """Map cloud provider HTTP status codes to stable gateway errors."""
    if status_code in {401, 403}:
        return GatewayError(f"{provider} authentication failed", retryable=False)
    if status_code == 429:
        return GatewayError(f"{provider} rate limited")
    if status_code >= 500:
        return GatewayError(f"{provider} provider unavailable")
    return GatewayError(f"{provider} request failed: HTTP {status_code}", retryable=False)


async def request_json(
    client: httpx.AsyncClient | None,
    method: str,
    url: str,
    timeout_seconds: float,
    headers: dict[str, str],
    payload: dict[str, object],
) -> dict[str, object]:
    """Run a cloud HTTP request and return a JSON object."""
    provider = _provider_from_url(url)
    try:
        if client is not None:
            response = await client.request(
                method,
                url,
                headers=headers,
                json=payload,
                timeout=timeout_seconds,
            )
        else:
            async with httpx.AsyncClient() as short_lived_client:
                response = await short_lived_client.request(
                    method,
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout_seconds,
                )
        if response.status_code >= 400:
            raise map_status_error(provider, response.status_code)
        try:
            body = response.json()
        except json.JSONDecodeError as error:
            raise GatewayError(f"{provider} malformed response", retryable=False) from error
    except GatewayError:
        raise
    except httpx.HTTPError as error:
        raise GatewayError(f"{provider} request failed: {error}") from error
    if not isinstance(body, dict):
        raise GatewayError(f"{provider} malformed response", retryable=False)
    return body


def _provider_from_url(url: str) -> str:
    """Infer a provider label for shared HTTP errors."""
    if "anthropic" in url:
        return "anthropic"
    if "deepseek" in url:
        return "deepseek"
    return "openai"
