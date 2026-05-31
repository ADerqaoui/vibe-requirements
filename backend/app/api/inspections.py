"""Spec inspection API routes."""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.gateway import GatewayFactory, get_gateway_factory
from app.config import get_settings
from app.db import get_db
from app.gateway.base import GatewayError
from app.inspector.parser import ParseFindingsError
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from app.schemas.inspection import InspectRequest, SpecInspectionOut
from app.services.gateway_service import GatewayRuntime
from app.services.inspector_service import (
    InspectorModelUnavailableError,
    SpecNotFoundError,
    get_enabled_inspector_model,
    inspect_spec,
    list_spec_inspections,
)

router = APIRouter(tags=["inspections"])


@router.post("/specs/{spec_id}/inspect", response_model=SpecInspectionOut)
async def inspect_spec_route(
    spec_id: int,
    payload: InspectRequest,
    db: Session = Depends(get_db),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
) -> SpecInspectionOut:
    """Run and persist one single-model inspection."""
    _ensure_spec_exists(db, spec_id)
    try:
        model = get_enabled_inspector_model(db, payload.model_id)
    except InspectorModelUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    settings = get_settings()
    try:
        gateway = gateway_factory(model, settings)
        row = await inspect_spec(
            db=db,
            spec_id=spec_id,
            model=model,
            gateway=gateway,
            runtime=GatewayRuntime(
                retry_count=settings.llm_retry_count,
                timeout_seconds=_timeout_for_provider(model.provider, settings),
            ),
        )
    except ParseFindingsError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except GatewayError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway failure: {error}",
        ) from error
    return _inspection_out(row)


@router.get("/specs/{spec_id}/inspections", response_model=list[SpecInspectionOut])
async def list_spec_inspections_route(
    spec_id: int,
    db: Session = Depends(get_db),
) -> list[SpecInspectionOut]:
    """List persisted inspections newest-first."""
    try:
        return [_inspection_out(row) for row in list_spec_inspections(db, spec_id)]
    except SpecNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found") from error


def _inspection_out(row: SpecInspection) -> SpecInspectionOut:
    """Map a persisted inspection row to the API response."""
    return SpecInspectionOut(
        id=row.id,
        spec_id=row.spec_id,
        model_id=row.model_id,
        findings=json.loads(row.findings),
        passes=row.passes,
        created_at=row.created_at,
    )


def _ensure_spec_exists(db: Session, spec_id: int) -> None:
    """Raise route-level 404 before model or gateway checks."""
    if db.get(Spec, spec_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found")


def _timeout_for_provider(provider: str, settings) -> float:
    """Return provider-specific timeout."""
    if provider == "ollama":
        return settings.ollama_timeout_seconds
    return settings.cloud_timeout_seconds
