"""Ollama local adapter."""
import httpx

from app.gateway.base import GatewayError, GatewayResult

CHAT_PATH = "/api/chat"
HEALTH_PATH = "/api/tags"


class OllamaGateway:
    """Gateway adapter for the local Ollama HTTP API."""

    def __init__(self, host: str, model_tag: str, client: httpx.AsyncClient | None = None):
        self._host = host.rstrip("/")
        self._model_tag = model_tag
        self._client = client

    async def health_check(self, timeout_seconds: float) -> None:
        """Verify the local Ollama service is reachable."""
        try:
            response = await self._request("GET", HEALTH_PATH, timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise GatewayError(f"ollama health check failed: {error}") from error

    async def complete(
        self,
        prompt: str,
        system: str | None,
        timeout_seconds: float,
    ) -> GatewayResult:
        """Send a non-streaming chat completion request to Ollama."""
        messages = []
        if system is not None and system.strip() != "":
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self._model_tag, "messages": messages, "stream": False}

        try:
            response = await self._request("POST", CHAT_PATH, timeout_seconds, json=payload)
            response.raise_for_status()
            return _parse_response(response.json())
        except GatewayError:
            raise
        except (ValueError, httpx.HTTPError) as error:
            raise GatewayError(f"ollama completion failed: {error}") from error

    async def _request(
        self,
        method: str,
        path: str,
        timeout_seconds: float,
        json: dict[str, object] | None = None,
    ) -> httpx.Response:
        """Run a request using an injected or short-lived client."""
        if self._client is not None:
            return await self._client.request(method, path, timeout=timeout_seconds, json=json)
        async with httpx.AsyncClient(base_url=self._host) as client:
            return await client.request(method, path, timeout=timeout_seconds, json=json)


def _parse_response(payload: dict[str, object]) -> GatewayResult:
    """Parse Ollama's chat response into the gateway contract."""
    message = payload.get("message")
    if not isinstance(message, dict):
        raise GatewayError("ollama response missing message")
    text = message.get("content")
    in_tokens = payload.get("prompt_eval_count")
    out_tokens = payload.get("eval_count")
    if not isinstance(text, str):
        raise GatewayError("ollama response missing text")
    if not isinstance(in_tokens, int) or not isinstance(out_tokens, int):
        raise GatewayError("ollama response missing token counts")
    return GatewayResult(text=text, in_tokens=in_tokens, out_tokens=out_tokens)
