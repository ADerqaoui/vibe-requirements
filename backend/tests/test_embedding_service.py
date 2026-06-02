"""Embedding service tests."""
import httpx
import pytest
from sqlalchemy.orm import Session

from app.config import Settings
from app.gateway.base import CostCeilingExceededError
from app.models.call_log import CallLog
from app.models.model import Model
from app.models.setting import Setting
from app.services.embedding_service import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_TAG,
    EmbeddingError,
    EmbeddingService,
)


def vector(value: float = 0.1) -> list[float]:
    """Return a deterministic embedding vector."""
    return [value] * EMBEDDING_DIMENSIONS


def settings() -> Settings:
    """Return test settings without reading environment files."""
    return Settings(
        ollama_host="http://ollama.test",
        ollama_timeout_seconds=7,
        llm_retry_count=1,
        _env_file=None,
    )


def seed_embedding_model(db_session: Session, enabled: int = 1) -> None:
    """Seed the required embedding model registry row."""
    db_session.add(
        Model(
            provider="ollama",
            name="Nomic Embed",
            ollama_tag=EMBEDDING_MODEL_TAG,
            tier="low",
            enabled=enabled,
        )
    )
    db_session.commit()


def seed_paid_embedding_model_over_ceiling(db_session: Session) -> None:
    """Seed a paid embedding model while monthly spend is at the ceiling."""
    db_session.add_all([
        Model(
            provider="ollama",
            name="Nomic Embed",
            ollama_tag=EMBEDDING_MODEL_TAG,
            tier="low",
            input_cost_per_1k=1,
            enabled=1,
        ),
        Setting(key="cost_ceiling_sek", value="1"),
        CallLog(task="manual", provider="openai", cost_sek=100, status="success"),
    ])
    db_session.commit()


@pytest.mark.asyncio
async def test_embedding_service_parses_ollama_embedding(db_session: Session) -> None:
    """A successful Ollama response returns the expected vector."""
    seed_embedding_model(db_session)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        return httpx.Response(200, json={"embedding": vector(0.2)})

    client = httpx.AsyncClient(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    service = EmbeddingService(db_session, settings(), client)

    result = await service.embed("Brake safely")

    await client.aclose()
    assert result == vector(0.2)
    assert [request.url.path for request in requests] == ["/api/tags", "/api/embeddings"]
    assert requests[1].read().decode() == '{"model":"nomic-embed-text","prompt":"Brake safely"}'


@pytest.mark.asyncio
async def test_embedding_service_rejects_missing_or_disabled_model(
    db_session: Session,
) -> None:
    """The embedding model must exist and be enabled."""
    service = EmbeddingService(db_session, settings())

    with pytest.raises(EmbeddingError, match="not registered or enabled"):
        await service.embed("Brake safely")

    seed_embedding_model(db_session, enabled=0)

    with pytest.raises(EmbeddingError, match="disabled"):
        await service.embed("Brake safely")


@pytest.mark.asyncio
async def test_embedding_service_retries_timeout_like_failures(
    db_session: Session,
) -> None:
    """Embedding calls retry with the configured timeout."""
    seed_embedding_model(db_session)
    attempts = 0
    timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        timeouts.append(float(request.extensions["timeout"]["connect"]))
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        attempts += 1
        if attempts == 1:
            raise httpx.TimeoutException("timeout", request=request)
        return httpx.Response(200, json={"embedding": vector(0.3)})

    client = httpx.AsyncClient(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    service = EmbeddingService(db_session, settings(), client)

    result = await service.embed("Brake safely")

    await client.aclose()
    assert result == vector(0.3)
    assert attempts == 2
    assert timeouts == [7, 7, 7, 7]


@pytest.mark.asyncio
async def test_embedding_service_blocks_paid_embedding_before_http(
    db_session: Session,
) -> None:
    """Paid embedding models are blocked before an HTTP attempt at the ceiling."""
    seed_paid_embedding_model_over_ceiling(db_session)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"embedding": vector(0.2)})

    client = httpx.AsyncClient(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    service = EmbeddingService(db_session, settings(), client)

    with pytest.raises(CostCeilingExceededError):
        await service.embed("Brake safely")

    await client.aclose()
    assert requests == []
