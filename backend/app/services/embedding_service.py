"""Ollama embedding service."""
from collections.abc import Sequence

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.model import Model

EMBEDDING_MODEL_TAG = "nomic-embed-text"
EMBEDDING_DIMENSIONS = 768
EMBEDDINGS_PATH = "/api/embeddings"
HEALTH_PATH = "/api/tags"


class EmbeddingError(Exception):
    """Raised when an embedding cannot be produced cleanly."""


class EmbeddingService:
    """Generate text embeddings through Ollama."""

    def __init__(
        self,
        db: Session,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ):
        self._db = db
        self._settings = settings
        self._client = client

    async def embed(self, text: str) -> list[float]:
        """Return the configured Ollama embedding for text."""
        model = self._embedding_model()
        return await self._embed_with_retries(
            model_tag=model.ollama_tag or EMBEDDING_MODEL_TAG,
            text=text,
            retry_count=self._settings.llm_retry_count,
            timeout_seconds=self._settings.ollama_timeout_seconds,
        )

    def _embedding_model(self) -> Model:
        model = self._db.scalar(
            select(Model).where(Model.ollama_tag == EMBEDDING_MODEL_TAG).limit(1)
        )
        if model is None:
            raise EmbeddingError(
                f"Embedding model '{EMBEDDING_MODEL_TAG}' is not registered or enabled"
            )
        if not bool(model.enabled):
            raise EmbeddingError(f"Embedding model '{EMBEDDING_MODEL_TAG}' is disabled")
        return model

    async def _embed_with_retries(
        self,
        model_tag: str,
        text: str,
        retry_count: int,
        timeout_seconds: float,
    ) -> list[float]:
        attempts = max(0, retry_count) + 1
        last_error: EmbeddingError | None = None
        for _attempt in range(attempts):
            try:
                await self._health_check(timeout_seconds)
                return await self._embed_once(model_tag, text, timeout_seconds)
            except EmbeddingError as error:
                last_error = error
        if last_error is None:
            raise EmbeddingError("embedding call failed")
        raise EmbeddingError(str(last_error)) from last_error

    async def _health_check(self, timeout_seconds: float) -> None:
        try:
            response = await self._request("GET", HEALTH_PATH, timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise EmbeddingError(f"ollama embedding health check failed: {error}") from error

    async def _embed_once(self, model_tag: str, text: str, timeout_seconds: float) -> list[float]:
        payload = {"model": model_tag, "prompt": text}
        try:
            response = await self._request("POST", EMBEDDINGS_PATH, timeout_seconds, json=payload)
            response.raise_for_status()
            return _parse_embedding(response.json())
        except EmbeddingError:
            raise
        except (ValueError, httpx.HTTPError) as error:
            raise EmbeddingError(f"ollama embedding failed: {error}") from error

    async def _request(
        self,
        method: str,
        path: str,
        timeout_seconds: float,
        json: dict[str, object] | None = None,
    ) -> httpx.Response:
        if self._client is not None:
            return await self._client.request(method, path, timeout=timeout_seconds, json=json)
        async with httpx.AsyncClient(base_url=self._settings.ollama_host) as client:
            return await client.request(method, path, timeout=timeout_seconds, json=json)


def _parse_embedding(payload: dict[str, object]) -> list[float]:
    embedding = payload.get("embedding")
    if not isinstance(embedding, Sequence) or isinstance(embedding, (str, bytes)):
        raise EmbeddingError("ollama embedding response missing embedding")
    values = [float(value) for value in embedding]
    if len(values) != EMBEDDING_DIMENSIONS:
        raise EmbeddingError(
            f"ollama embedding returned {len(values)} dimensions; expected {EMBEDDING_DIMENSIONS}"
        )
    return values
