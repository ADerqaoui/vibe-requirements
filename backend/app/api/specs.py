"""Specs API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.spec import Spec
from app.schemas.spec import SpecCreate, SpecOut
from app.services.need_service import NeedNotFoundError
from app.services.spec_service import (
    SpecLayerNotFoundError,
    SpecNotFoundError,
    create_spec_for_parent_spec,
    create_spec_for_need,
    list_children_of_spec,
    list_specs_for_need,
)

router = APIRouter(tags=["specs"])


@router.get("/needs/{need_id}/specs", response_model=list[SpecOut])
async def list_specs_route(need_id: int, db: Session = Depends(get_db)) -> list[SpecOut]:
    """List specs under a Need."""
    try:
        return [_spec_out(spec) for spec in list_specs_for_need(db, need_id)]
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error


@router.post("/needs/{need_id}/specs", response_model=SpecOut, status_code=status.HTTP_201_CREATED)
async def create_spec_route(
    need_id: int,
    payload: SpecCreate,
    db: Session = Depends(get_db),
) -> SpecOut:
    """Create a spec under a Need."""
    try:
        return _spec_out(create_spec_for_need(db, need_id, payload.statement))
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error
    except SpecLayerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Default spec layer not found",
        ) from error


@router.get("/specs/{spec_id}/specs", response_model=list[SpecOut])
async def list_child_specs_route(spec_id: int, db: Session = Depends(get_db)) -> list[SpecOut]:
    """List direct child Specs under a Spec."""
    try:
        return [_spec_out(spec) for spec in list_children_of_spec(db, spec_id)]
    except SpecNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found") from error


@router.post("/specs/{spec_id}/specs", response_model=SpecOut, status_code=status.HTTP_201_CREATED)
async def create_child_spec_route(
    spec_id: int,
    payload: SpecCreate,
    db: Session = Depends(get_db),
) -> SpecOut:
    """Create a child Spec under a Spec."""
    try:
        return _spec_out(create_spec_for_parent_spec(db, spec_id, payload.statement))
    except SpecNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found") from error
    except SpecLayerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Default spec layer not found",
        ) from error


def _spec_out(spec: Spec) -> SpecOut:
    """Map ORM fields to the slice API shape."""
    return SpecOut(
        id=spec.id,
        need_id=spec.need_id,
        statement=spec.text,
        complexity=spec.complexity,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )
