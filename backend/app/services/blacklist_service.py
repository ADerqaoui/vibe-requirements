"""Parent-scoped blacklist service."""
import json
import math
from typing import Literal, Protocol

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.blacklist_entry import BlacklistEntry
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.services.embedding_service import EMBEDDING_DIMENSIONS, EmbeddingError, EmbeddingService

ParentKind = Literal["need", "spec"]
BLACKLIST_SOURCE_REJECTED = "rejected"
BLACKLIST_SIMILARITY_THRESHOLD = 0.85
REFERENCE_MODELS = (Layer, Model, Prompt)


class BlacklistParentNotFoundError(Exception):
    """Raised when a blacklist parent is missing."""


class Embedder(Protocol):
    """Minimal embedding contract for blacklist operations."""

    async def embed(self, text: str) -> list[float]:
        """Return an embedding for text."""


class BlacklistService:
    """Persist and apply parent-scoped blacklist entries."""

    def __init__(self, db: Session, embedding_service: Embedder):
        self._db = db
        self._embedding_service = embedding_service

    async def add_blacklist_entry(
        self,
        parent_kind: ParentKind,
        parent_id: int,
        statement: str,
    ) -> BlacklistEntry:
        """Insert a blacklist row and matching vector atomically."""
        _ensure_parent_exists(self._db, parent_kind, parent_id)
        entry = BlacklistEntry(
            parent_need_id=parent_id if parent_kind == "need" else None,
            parent_spec_id=parent_id if parent_kind == "spec" else None,
            text=statement,
            source=BLACKLIST_SOURCE_REJECTED,
        )
        try:
            self._db.add(entry)
            self._db.flush()
            embedding = await self._embedding_service.embed(statement)
            _validate_embedding(embedding)
            _insert_vector(self._db, entry.id, embedding)
            self._db.commit()
            self._db.refresh(entry)
            return entry
        except Exception:
            self._db.rollback()
            raise

    def list_entries(self, parent_kind: ParentKind, parent_id: int) -> list[BlacklistEntry]:
        """List parent-scoped blacklist entries newest first."""
        _ensure_parent_exists(self._db, parent_kind, parent_id)
        return list(
            self._db.scalars(
                select(BlacklistEntry)
                .where(_parent_condition(parent_kind, parent_id))
                .order_by(BlacklistEntry.created_at.desc(), BlacklistEntry.id.desc())
            )
        )

    async def filter_against_blacklist(
        self,
        parent_kind: ParentKind,
        parent_id: int,
        candidates: list[str],
    ) -> list[str]:
        """Drop candidates whose max cosine similarity reaches the blacklist threshold."""
        blacklist_vectors = _list_vectors(self._db, parent_kind, parent_id)
        if len(blacklist_vectors) == 0:
            return candidates

        surviving_candidates: list[str] = []
        for candidate in candidates:
            candidate_vector = await self._embedding_service.embed(candidate)
            _validate_embedding(candidate_vector)
            max_similarity = max(
                _cosine_similarity(candidate_vector, blacklist_vector)
                for blacklist_vector in blacklist_vectors
            )
            if max_similarity < BLACKLIST_SIMILARITY_THRESHOLD:
                surviving_candidates.append(candidate)
        return surviving_candidates


def _ensure_parent_exists(db: Session, parent_kind: ParentKind, parent_id: int) -> None:
    model_class = Need if parent_kind == "need" else Spec
    if db.get(model_class, parent_id) is None:
        raise BlacklistParentNotFoundError


def _parent_condition(parent_kind: ParentKind, parent_id: int):
    if parent_kind == "need":
        return BlacklistEntry.parent_need_id == parent_id
    return BlacklistEntry.parent_spec_id == parent_id


def _insert_vector(db: Session, entry_id: int, embedding: list[float]) -> None:
    _ensure_sqlite_vec_loaded(db)
    db.execute(
        text("INSERT INTO blacklist_vec (entry_id, embedding) VALUES (:entry_id, :embedding)"),
        {"entry_id": entry_id, "embedding": json.dumps(embedding)},
    )


def _list_vectors(db: Session, parent_kind: ParentKind, parent_id: int) -> list[list[float]]:
    _ensure_sqlite_vec_loaded(db)
    parent_column = "parent_need_id" if parent_kind == "need" else "parent_spec_id"
    rows = db.execute(
        text(
            f"""
            SELECT vec_to_json(blacklist_vec.embedding)
            FROM blacklist_entries
            JOIN blacklist_vec ON blacklist_vec.entry_id = blacklist_entries.id
            WHERE blacklist_entries.{parent_column} = :parent_id
            """
        ),
        {"parent_id": parent_id},
    ).all()
    return [json.loads(row[0]) for row in rows]


def _ensure_sqlite_vec_loaded(db: Session) -> None:
    raw_connection = db.connection().connection.driver_connection
    try:
        import sqlite_vec

        raw_connection.enable_load_extension(True)
        sqlite_vec.load(raw_connection)
    except Exception as error:
        raise EmbeddingError(f"sqlite-vec extension could not be loaded: {error}") from error
    finally:
        raw_connection.enable_load_extension(False)


def _validate_embedding(embedding: list[float]) -> None:
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise EmbeddingError(
            f"Embedding returned {len(embedding)} dimensions; expected {EMBEDDING_DIMENSIONS}"
        )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot_product / (left_norm * right_norm)


def build_blacklist_service(db: Session, embedding_service: EmbeddingService) -> BlacklistService:
    """Create the production blacklist service."""
    return BlacklistService(db, embedding_service)
