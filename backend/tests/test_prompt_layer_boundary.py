"""Explicit prompt layer-boundary tests."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.api.gateway import get_gateway_factory
from app.db import get_db
from app.gateway.base import GatewayResult
from app.models.layer import Layer
from app.models.model import Model
from app.models.need import Need
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.spec import Spec
from app.seed.run import seed_reference_data
from app.services.prompt_errors import PromptLayerMismatchError
from app.services.prompt_selection import PromptSelectionContext
from app.services.prompt_service import select_prompt


class FakeGateway:
    """Fake gateway for prompt-boundary API tests."""

    async def health_check(self, timeout_seconds: float) -> None:
        pass

    async def complete(self, prompt: str, system: str | None, timeout_seconds: float) -> GatewayResult:
        if "inspect" in prompt.lower():
            return GatewayResult(
                "- Clarity: PASS — clear\n"
                "- Measurability: PASS — measurable\n"
                "- Testability: PASS — testable\n"
                "- Atomicity: PASS — one thing\n"
                "- Ambiguity-free: PASS — precise",
                5,
                5,
            )
        return GatewayResult("1. Brake", 5, 5)


def use_db_session(api_app: FastAPI, db_session: Session) -> None:
    """Use assertion session in API requests."""

    async def override_get_db():
        yield db_session

    api_app.dependency_overrides[get_db] = override_get_db


def seed_layers(db_session: Session) -> tuple[Layer, Layer]:
    seed_reference_data(db_session)
    first = db_session.query(Layer).filter_by(name="System Requirement").one()
    second = db_session.query(Layer).filter_by(name="System Architecture").one()
    return first, second


def seed_parent_and_model(db_session: Session) -> tuple[int, int, Layer, Layer]:
    layer_a, layer_b = seed_layers(db_session)
    project = Project(name="Demo")
    model = Model(provider="ollama", name="qwen", ollama_tag="qwen", tier="mid", enabled=1)
    db_session.add(project)
    db_session.flush()
    need = Need(project_id=project.id, statement="Stop safely")
    db_session.add_all([need, model])
    db_session.flush()
    db_session.commit()
    return need.id, model.id, layer_a, layer_b


def seed_spec_and_model(db_session: Session) -> tuple[int, int, Layer, Layer]:
    need_id, model_id, layer_a, layer_b = seed_parent_and_model(db_session)
    spec = Spec(need_id=need_id, layer_id=layer_a.id, text="The system shall brake.", source="ai")
    db_session.add(spec)
    db_session.flush()
    db_session.commit()
    return spec.id, model_id, layer_a, layer_b


@pytest.mark.asyncio
async def test_select_prompt_rejects_other_specific_layer(db_session: Session) -> None:
    """Explicit prompt ids cannot cross specific layer boundaries."""
    layer_a, layer_b = seed_layers(db_session)
    prompt_a = Prompt(task="task", name="A", layer_id=layer_a.id, version=1, enabled=1, template="A")
    prompt_b = Prompt(task="task", name="B", layer_id=layer_b.id, version=1, enabled=1, template="B")
    db_session.add_all([prompt_a, prompt_b])
    db_session.commit()

    with pytest.raises(PromptLayerMismatchError):
        select_prompt(db_session, "task", layer_a.id, PromptSelectionContext(prompt_id=prompt_b.id))


@pytest.mark.asyncio
async def test_generation_api_rejects_other_layer_prompt_id(api_app: FastAPI, db_session: Session) -> None:
    """Generation maps wrong specific-layer prompt ids to 422."""
    need_id, model_id, layer_a, layer_b = seed_parent_and_model(db_session)
    prompt = Prompt(
        task="generate_need_to_spec",
        name="Other layer",
        layer_id=layer_b.id,
        version=1,
        enabled=1,
        template="{parent_statement} {count}",
    )
    db_session.add(prompt)
    db_session.commit()
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": model_id, "prompt_id": prompt.id, "count": 1, "target_layer_id": layer_a.id},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "prompt does not belong to the target layer"


@pytest.mark.asyncio
async def test_inspection_api_rejects_other_layer_prompt_id(api_app: FastAPI, db_session: Session) -> None:
    """Inspection maps wrong specific-layer prompt ids to 422."""
    spec_id, model_id, _layer_a, layer_b = seed_spec_and_model(db_session)
    prompt = Prompt(
        task="inspect_spec",
        name="Other layer",
        layer_id=layer_b.id,
        version=1,
        enabled=1,
        template="Inspect {spec_statement}",
    )
    db_session.add(prompt)
    db_session.commit()
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/specs/{spec_id}/inspect", json={"model_id": model_id, "prompt_id": prompt.id})

    assert response.status_code == 422
    assert response.json()["detail"] == "prompt does not belong to the target layer"


@pytest.mark.asyncio
async def test_global_prompt_id_is_allowed_for_specific_generation_layer(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    """A global explicit prompt remains a valid layer fallback."""
    need_id, model_id, layer_a, _layer_b = seed_parent_and_model(db_session)
    prompt = Prompt(
        task="generate_need_to_spec",
        name="Global",
        version=1,
        enabled=1,
        template="Global {parent_statement} {count}",
    )
    db_session.add(prompt)
    db_session.commit()
    use_db_session(api_app, db_session)

    async def override_gateway_factory():
        return lambda _model, _settings: FakeGateway()

    api_app.dependency_overrides[get_gateway_factory] = override_gateway_factory
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/needs/{need_id}/generate",
            json={"model_id": model_id, "prompt_id": prompt.id, "count": 1, "target_layer_id": layer_a.id},
        )

    assert response.status_code == 200
    assert response.json()["selected_prompt_id"] == prompt.id


@pytest.mark.asyncio
async def test_prompt_variants_api_returns_layer_and_global_scope(
    api_app: FastAPI,
    db_session: Session,
) -> None:
    layer_a, _layer_b = seed_layers(db_session)
    global_prompt = Prompt(task="task", name="Global", version=1, enabled=1, template="global")
    layer_prompt = Prompt(task="task", name="Layer", layer_id=layer_a.id, version=1, enabled=1, template="layer")
    db_session.add_all([global_prompt, layer_prompt])
    db_session.commit()
    use_db_session(api_app, db_session)

    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/prompts/task/variants?layer_id={layer_a.id}")

    assert response.status_code == 200
    body = response.json()
    assert {(item["name"], item["scope_label"]) for item in body} == {
        ("Global", "Global"),
        ("Layer", "System Requirement"),
    }
    assert [item["name"] for item in body if item["is_default"]] == ["Layer"]
