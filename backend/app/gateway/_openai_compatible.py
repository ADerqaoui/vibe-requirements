"""OpenAI-compatible cloud chat adapter."""
import httpx

from app.gateway._cloud_http import DEFAULT_MAX_TOKENS, request_json
from app.gateway.base import GatewayError, GatewayResult

CHAT_COMPLETIONS_PATH = "/chat/completions"


class OpenAICompatibleGateway:
    """Gateway adapter for OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        provider: str,
        base_url: str,
        api_key: str,
        api_model_id: str,
        client: httpx.AsyncClient | None = None,
    ):
        self._provider = provider
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._api_model_id = api_model_id
        self._client = client

    async def health_check(self, timeout_seconds: float) -> None:
        """Cloud providers skip pre-call health checks."""

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Send a non-streaming OpenAI-compatible chat completion request."""
        messages = []
        if system is not None and system.strip() != "":
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self._api_model_id,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "messages": messages,
        }
        body = await request_json(
            client=self._client,
            method="POST",
            url=f"{self._base_url}{CHAT_COMPLETIONS_PATH}",
            timeout_seconds=timeout_seconds,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
        )
        return self._parse_response(body)

    def _parse_response(self, payload: dict[str, object]) -> GatewayResult:
        choices = payload.get("choices")
        usage = payload.get("usage")
        if not isinstance(choices, list) or not choices:
            raise GatewayError(f"{self._provider} malformed response", retryable=False)
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise GatewayError(f"{self._provider} malformed response", retryable=False)
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise GatewayError(f"{self._provider} malformed response", retryable=False)
        text = message.get("content")
        if not isinstance(usage, dict) or not isinstance(text, str):
            raise GatewayError(f"{self._provider} malformed response", retryable=False)
        in_tokens = usage.get("prompt_tokens")
        out_tokens = usage.get("completion_tokens")
        if not isinstance(in_tokens, int) or not isinstance(out_tokens, int):
            raise GatewayError(f"{self._provider} malformed response", retryable=False)
        return GatewayResult(text=text, in_tokens=in_tokens, out_tokens=out_tokens)
