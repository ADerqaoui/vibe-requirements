"""Anthropic cloud adapter."""
import httpx

from app.gateway._cloud_http import DEFAULT_MAX_TOKENS, request_json
from app.gateway._cloud_http import require_api_key, require_api_model_id
from app.gateway.base import GatewayError, GatewayResult

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicGateway:
    """Gateway adapter for Anthropic messages."""

    def __init__(
        self,
        api_key: str,
        api_model_id: str | None,
        client: httpx.AsyncClient | None = None,
    ):
        self._api_key = require_api_key(api_key, "anthropic")
        self._api_model_id = require_api_model_id(api_model_id, "anthropic")
        self._client = client

    async def health_check(self, timeout_seconds: float) -> None:
        """Cloud providers skip pre-call health checks."""

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Send a non-streaming Anthropic messages request."""
        payload: dict[str, object] = {
            "model": self._api_model_id,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None and system.strip() != "":
            payload["system"] = system
        body = await request_json(
            client=self._client,
            method="POST",
            url=ANTHROPIC_MESSAGES_URL,
            timeout_seconds=timeout_seconds,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            payload=payload,
        )
        return _parse_response(body)


def _parse_response(payload: dict[str, object]) -> GatewayResult:
    """Parse Anthropic's messages response into the gateway contract."""
    content = payload.get("content")
    usage = payload.get("usage")
    if not isinstance(content, list) or not content:
        raise GatewayError("anthropic malformed response", retryable=False)
    first_content = content[0]
    if not isinstance(first_content, dict):
        raise GatewayError("anthropic malformed response", retryable=False)
    text = first_content.get("text")
    if not isinstance(usage, dict) or not isinstance(text, str):
        raise GatewayError("anthropic malformed response", retryable=False)
    in_tokens = usage.get("input_tokens")
    out_tokens = usage.get("output_tokens")
    if not isinstance(in_tokens, int) or not isinstance(out_tokens, int):
        raise GatewayError("anthropic malformed response", retryable=False)
    return GatewayResult(text=text, in_tokens=in_tokens, out_tokens=out_tokens)
