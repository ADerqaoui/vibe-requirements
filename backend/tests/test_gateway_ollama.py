"""Ollama gateway adapter tests."""
import httpx
import pytest

from app.gateway.base import GatewayError
from app.gateway.ollama import OllamaGateway


@pytest.mark.asyncio
async def test_ollama_adapter_parses_text_and_tokens() -> None:
    """Recorded Ollama-style response maps to gateway result."""

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        assert request.url.path == "/api/chat"
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "hello"},
                "prompt_eval_count": 7,
                "eval_count": 3,
            },
        )

    client = httpx.AsyncClient(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    gateway = OllamaGateway("http://ollama.test", "qwen2.5:7b", client)

    await gateway.health_check(1)
    result = await gateway.complete("Say hi", None, 1)
    await client.aclose()

    assert result.text == "hello"
    assert result.in_tokens == 7
    assert result.out_tokens == 3


@pytest.mark.asyncio
async def test_ollama_adapter_rejects_malformed_response() -> None:
    """Malformed Ollama payloads become clean GatewayError values."""

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "missing tokens"}})

    client = httpx.AsyncClient(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    gateway = OllamaGateway("http://ollama.test", "qwen2.5:7b", client)

    with pytest.raises(GatewayError, match="token counts"):
        await gateway.complete("Say hi", None, 1)
    await client.aclose()
