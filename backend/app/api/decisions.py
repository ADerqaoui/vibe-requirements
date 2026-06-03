"""Spec lifecycle decision API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.spec import Spec
from app.schemas.decision import DecisionRequest
from app.schemas.spec import SpecOut
from app.services.decision_service import SpecNotFoundError, decide_spec
from app.services.spec_service import latest_inspection_ids

router = APIRouter(tags=["decisions"])


@router.post("/specs/{spec_id}/decision", response_model=SpecOut)
async def decide_spec_route(
    spec_id: int,
    payload: DecisionRequest,
    db: Session = Depends(get_db),
) -> SpecOut:
    """Accept or reject a Spec."""
    try:
        spec = decide_spec(db, spec_id, payload.decision)
    except SpecNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found") from error
    latest_id = latest_inspection_ids(db, [spec.id]).get(spec.id)
    return _spec_out(spec, latest_id)


def _spec_out(spec: Spec, latest_inspection_id: int | None) -> SpecOut:
    """Map ORM fields to the Spec API shape."""
    return SpecOut(
        id=spec.id,
        need_id=spec.need_id,
        parent_spec_id=spec.parent_spec_id,
        layer_id=spec.layer_id,
        layer_name=spec.layer.name if spec.layer is not None else "",
        statement=spec.text,
        complexity=spec.complexity,
        status=spec.status,
        latest_inspection_id=latest_inspection_id,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )
