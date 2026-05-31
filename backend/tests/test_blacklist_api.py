"""Blacklist API tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.blacklist import get_blacklist_service
from app.db import get_db
from app.models.layer import Layer
from app.models.need import Need
from app.models.project import Project
from app.models.spec import Spec
from app.services.blacklist_service import BlacklistService
from app.services.embedding_service import EMBEDDING_DIMENSIONS, EmbeddingError


class FakeEmbeddingService:
    """Embedding fake for API tests."""

    def __init__(self, failures: set[str] | None = None):
        self.failures = failures or set()

    async def embed(self, text_value: str) -> list[float]:
        if text_value in self.failures:
            raise EmbeddingError("embed down")
        return [0.1] * EMBEDDING_DIMENSIONS


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def use_blacklist_service(
    api_app: FastAPI,
    db_session: Session,
    fake_embedding_service: FakeEmbeddingService,
) -> None:
    """Use a fake embedding-backed blacklist service."""

    async def override_get_blacklist_service():
        return BlacklistService(db_session, fake_embedding_service)

    api_app.dependency_overrides[get_blacklist_service] = override_get_blacklist_service


def seed_parents(db_session: Session) -> tuple[int, int, int]:
    """Seed Need and Spec parents."""
    project = Project(name="Demo")
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Need parent")
    layer = Layer(name="System Requirement", kind="cross_cutting", sort_order=10)
    db_session.add_all([need, layer])
    db_session.flush()
    spec = Spec(need_id=need.id, layer_id=layer.id, text="Spec parent", source="ai")
    db_session.add(spec)
    db_session.flush()
    ids = (project.id, need.id, spec.id)
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
async def test_blacklist_api_creates_need_and_spec_entries(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """Create routes persist entries and vectors with the response shape."""
    _, need_id, spec_id = seed_parents(db_session)
    use_db_session(api_app, db_session)
    use_blacklist_service(api_app, db_session, FakeEmbeddingService())

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        need_response = await client.post(
            f"/api/needs/{need_id}/blacklist",
            json={"statement": "Rejected need candidate"},
        )
        spec_response = await client.post(
            f"/api/specs/{spec_id}/blacklist",
            json={"statement": "Rejected spec candidate"},
        )

    assert need_response.status_code == 201
    assert spec_response.status_code == 201
    assert need_response.json().items() >= {
        "parent_need_id": need_id,
        "parent_spec_id": None,
        "text": "Rejected need candidate",
        "source": "rejected",
    }.items()
    assert spec_response.json().items() >= {
        "parent_need_id": None,
        "parent_spec_id": spec_id,
        "text": "Rejected spec candidate",
        "source": "rejected",
    }.items()
    assert db_session.scalar(text("SELECT COUNT(*) FROM blacklist_entries")) == 2
    assert db_session.scalar(text("SELECT COUNT(*) FROM blacklist_vec")) == 2


@pytest.mark.asyncio
async def test_blacklist_api_get_returns_newest_first_and_scoped(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """GET returns only the requested parent's entries newest first."""
    _, need_id, spec_id = seed_parents(db_session)
    use_db_session(api_app, db_session)
    use_blacklist_service(api_app, db_session, FakeEmbeddingService())

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            f"/api/needs/{need_id}/blacklist",
            json={"statement": "Old need candidate"},
        )
        second = await client.post(
            f"/api/needs/{need_id}/blacklist",
            json={"statement": "New need candidate"},
        )
        await client.post(
            f"/api/specs/{spec_id}/blacklist",
            json={"statement": "Spec candidate"},
        )
        need_list = await client.get(f"/api/needs/{need_id}/blacklist")
        spec_list = await client.get(f"/api/specs/{spec_id}/blacklist")

    assert first.status_code == 201
    assert second.status_code == 201
    assert [entry["text"] for entry in need_list.json()] == [
        "New need candidate",
        "Old need candidate",
    ]
    assert [entry["text"] for entry in spec_list.json()] == ["Spec candidate"]


@pytest.mark.asyncio
async def test_blacklist_api_errors_and_embed_failure_rolls_back(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """API returns 404, 422, and 502 without orphan writes."""
    _, need_id, _ = seed_parents(db_session)
    use_db_session(api_app, db_session)
    use_blacklist_service(
        api_app,
        db_session,
        FakeEmbeddingService({"Embed failure"}),
    )

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.post("/api/needs/999/blacklist", json={"statement": "x"})
        blank = await client.post(f"/api/needs/{need_id}/blacklist", json={"statement": "   "})
        failure = await client.post(
            f"/api/needs/{need_id}/blacklist",
            json={"statement": "Embed failure"},
        )

    assert missing.status_code == 404
    assert blank.status_code == 422
    assert failure.status_code == 502
    assert "Embedding failure" in failure.json()["detail"]
    load_sqlite_vec(db_session)
    assert db_session.scalar(text("SELECT COUNT(*) FROM blacklist_entries")) == 0
    assert db_session.scalar(text("SELECT COUNT(*) FROM blacklist_vec")) == 0
