"""Blacklist service tests."""
import math

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.services.blacklist_service import BlacklistService
from app.services.embedding_service import EMBEDDING_DIMENSIONS, EmbeddingError


class FakeEmbeddingService:
    """Embedding fake keyed by text."""

    def __init__(self, embeddings: dict[str, list[float]], failing_texts: set[str] | None = None):
        self.embeddings = embeddings
        self.failing_texts = failing_texts or set()
        self.calls: list[str] = []

    async def embed(self, text_value: str) -> list[float]:
        self.calls.append(text_value)
        if text_value in self.failing_texts:
            raise EmbeddingError("embed down")
        return self.embeddings[text_value]


def unit_vector(first: float, second: float = 0.0) -> list[float]:
    """Return a 768-dim vector using the first two axes."""
    return [first, second, *([0.0] * (EMBEDDING_DIMENSIONS - 2))]


def cosine_vector(similarity: float) -> list[float]:
    """Return a unit vector with requested cosine against axis one."""
    return unit_vector(similarity, math.sqrt(1 - similarity * similarity))


def seed_parents(db_session: Session) -> tuple[int, int, int, int]:
    """Seed two Needs and one Spec parent."""
    project = Project(name="Demo")
    db_session.add(project)
    db_session.flush()
    need_one = Need(project_id=project.id, statement="Need one")
    need_two = Need(project_id=project.id, statement="Need two")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([need_one, need_two, layer])
    db_session.flush()
    spec = Spec(need_id=need_one.id, layer_id=layer.id, text="Spec parent", source="ai")
    db_session.add(spec)
    db_session.flush()
    ids = (need_one.id, need_two.id, spec.id, layer.id)
    db_session.commit()
    return ids


def load_sqlite_vec(db_session: Session) -> None:
    """Load sqlite-vec on the assertion connection before direct vector queries."""
    import sqlite_vec

    raw_connection = db_session.connection().connection.driver_connection
    raw_connection.enable_load_extension(True)
    sqlite_vec.load(raw_connection)
    raw_connection.enable_load_extension(False)


@pytest.mark.asyncio
async def test_blacklist_add_writes_entry_and_vector(db_session: Session) -> None:
    """Adding a blacklist entry persists both rows atomically."""
    need_id, _, _, _ = seed_parents(db_session)
    service = BlacklistService(
        db_session,
        FakeEmbeddingService({"Rejected brake": unit_vector(1)}),
    )

    entry = await service.add_blacklist_entry("need", need_id, "Rejected brake")

    vector_count = db_session.scalar(text("SELECT COUNT(*) FROM blacklist_vec"))
    assert entry.id is not None
    assert entry.parent_need_id == need_id
    assert entry.parent_spec_id is None
    assert entry.source == "rejected"
    assert vector_count == 1


@pytest.mark.asyncio
async def test_blacklist_list_scopes_by_parent_and_newest_first(db_session: Session) -> None:
    """Need and Spec blacklist entries stay isolated and list newest first."""
    need_one_id, need_two_id, spec_id, _ = seed_parents(db_session)
    service = BlacklistService(
        db_session,
        FakeEmbeddingService(
            {
                "Need one old": unit_vector(1),
                "Need one new": unit_vector(1),
                "Need two": unit_vector(1),
                "Spec only": unit_vector(1),
            }
        ),
    )

    first_entry = await service.add_blacklist_entry("need", need_one_id, "Need one old")
    second_entry = await service.add_blacklist_entry("need", need_one_id, "Need one new")
    await service.add_blacklist_entry("need", need_two_id, "Need two")
    await service.add_blacklist_entry("spec", spec_id, "Spec only")

    need_one_entries = service.list_entries("need", need_one_id)
    need_two_entries = service.list_entries("need", need_two_id)
    spec_entries = service.list_entries("spec", spec_id)

    assert [entry.id for entry in need_one_entries] == [second_entry.id, first_entry.id]
    assert [entry.text for entry in need_two_entries] == ["Need two"]
    assert [entry.text for entry in spec_entries] == ["Spec only"]


@pytest.mark.asyncio
async def test_blacklist_add_rolls_back_on_embed_failure(db_session: Session) -> None:
    """Embedding failures leave no orphan blacklist entry."""
    need_id, _, _, _ = seed_parents(db_session)
    service = BlacklistService(
        db_session,
        FakeEmbeddingService({"Rejected brake": unit_vector(1)}, {"Rejected brake"}),
    )

    with pytest.raises(EmbeddingError, match="embed down"):
        await service.add_blacklist_entry("need", need_id, "Rejected brake")

    load_sqlite_vec(db_session)
    entry_count = db_session.scalar(text("SELECT COUNT(*) FROM blacklist_entries"))
    vector_count = db_session.scalar(text("SELECT COUNT(*) FROM blacklist_vec"))
    assert entry_count == 0
    assert vector_count == 0


@pytest.mark.asyncio
async def test_filter_against_blacklist_drops_close_candidates(db_session: Session) -> None:
    """Close candidates are blocked while far candidates survive."""
    need_id, _, _, _ = seed_parents(db_session)
    fake_embeddings = FakeEmbeddingService(
        {
            "Rejected brake": unit_vector(1),
            "Close brake": cosine_vector(0.99),
            "Far alert": unit_vector(0, 1),
        }
    )
    service = BlacklistService(db_session, fake_embeddings)
    await service.add_blacklist_entry("need", need_id, "Rejected brake")

    result = await service.filter_against_blacklist(
        "need",
        need_id,
        ["Close brake", "Far alert"],
    )

    assert result == ["Far alert"]


@pytest.mark.asyncio
async def test_filter_threshold_boundary_and_empty_blacklist(db_session: Session) -> None:
    """The hard threshold keeps 0.849 and drops 0.851; empty blacklist is unchanged."""
    need_id, need_two_id, _, _ = seed_parents(db_session)
    fake_embeddings = FakeEmbeddingService(
        {
            "Rejected brake": unit_vector(1),
            "Keep boundary": cosine_vector(0.849),
            "Drop boundary": cosine_vector(0.851),
        }
    )
    service = BlacklistService(db_session, fake_embeddings)
    await service.add_blacklist_entry("need", need_id, "Rejected brake")

    filtered = await service.filter_against_blacklist(
        "need",
        need_id,
        ["Keep boundary", "Drop boundary"],
    )
    unfiltered = await service.filter_against_blacklist(
        "need",
        need_two_id,
        ["Drop boundary"],
    )

    assert filtered == ["Keep boundary"]
    assert unfiltered == ["Drop boundary"]
