"""Single-model Spec inspector service."""
from __future__ import annotations

import json

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.gateway.base import Gateway, GatewayError
from app.inspector.parser import ParseFindingsError, parse_findings
from app.inspector.prompts import make_inspect_prompt
from app.models.model import Model
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from app.services.model_service import ModelNotFoundError, get_model
from app.services.gateway_service import GatewayRuntime, complete_model


class SpecNotFoundError(Exception):
    """Raised when a Spec does not exist."""


class InspectorModelUnavailableError(Exception):
    """Raised when the requested inspection model is missing or disabled."""


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
) -> SpecInspection:
    """Run one inspection and persist the parsed findings."""
    spec = db.get(Spec, spec_id)
    if spec is None:
        raise SpecNotFoundError
    prompt = make_inspect_prompt(spec.text)
    try:
        completion = await complete_model(
            db=db,
            model=model,
            gateway=gateway,
            prompt=prompt,
            system=None,
            runtime=runtime,
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
