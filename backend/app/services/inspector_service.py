"""Single-model Spec inspector service."""
from __future__ import annotations

import json

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.gateway.base import Gateway, GatewayError
from app.inspector.parser import ParseFindingsError, parse_findings
from app.models.model import Model
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from app.services.model_service import ModelNotFoundError, get_model
from app.services.gateway_service import GatewayRuntime, complete_model
from app.services.prompt_selection import PromptSelectionContext
from app.services.prompt_service import render_prompt, select_prompt
from app.services.router_service import is_router_enabled, select_model


class SpecNotFoundError(Exception):
    """Raised when a Spec does not exist."""


class InspectorModelUnavailableError(Exception):
    """Raised when the requested inspection model is missing or disabled."""


def resolve_inspector_model(db: Session, model_id: int | None) -> Model:
    """Resolve the model for inspection, using router mode when enabled."""
    if is_router_enabled(db):
        return select_model(db, "inspect_spec")
    if model_id is None:
        raise InspectorModelUnavailableError("Model is required")
    return get_enabled_inspector_model(db, model_id)


def get_enabled_inspector_model(db: Session, model_id: int) -> Model:
    """Return an enabled inspector model or raise a service-level error."""
    try:
        model = get_model(db, model_id)
    except ModelNotFoundError as error:
        raise InspectorModelUnavailableError("Model not found") from error
    if not bool(model.enabled):
        raise InspectorModelUnavailableError("Model is disabled")
    return model


async def inspect_spec(
    db: Session,
    spec_id: int,
    model: Model,
    gateway: Gateway,
    runtime: GatewayRuntime,
    prompt_id: int | None = None,
) -> SpecInspection:
    """Run one inspection and persist the parsed findings."""
    spec = db.get(Spec, spec_id)
    if spec is None:
        raise SpecNotFoundError
    selected_prompt = select_prompt(
        db,
        "inspect_spec",
        layer_id=spec.layer_id,
        context=PromptSelectionContext(prompt_id=prompt_id, parent_kind="spec", parent_id=spec_id, layer_id=spec.layer_id),
    )
    prompt = render_prompt(selected_prompt, spec_statement=spec.text)
    try:
        completion = await complete_model(
            db=db,
            model=model,
            gateway=gateway,
            prompt=prompt.text,
            system=None,
            runtime=runtime,
            prompt_id=prompt.prompt_id,
            prompt_version=prompt.prompt_version,
        )
        findings = parse_findings(completion.text)
    except GatewayError:
        raise
    except ParseFindingsError:
        raise

    row = SpecInspection(
        spec_id=spec.id,
        model_id=model.id,
        findings=json.dumps(findings, separators=(",", ":")),
        summary=findings["summary"],
        passes=1,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    row.selected_prompt_id = prompt.prompt_id
    row.selected_prompt_name = prompt.prompt_name
    return row


def list_spec_inspections(db: Session, spec_id: int) -> list[SpecInspection]:
    """Return past inspections newest-first for one Spec."""
    if db.get(Spec, spec_id) is None:
        raise SpecNotFoundError
    statement = (
        select(SpecInspection)
        .where(SpecInspection.spec_id == spec_id)
        .order_by(desc(SpecInspection.created_at), desc(SpecInspection.id))
    )
    return list(db.scalars(statement).all())
