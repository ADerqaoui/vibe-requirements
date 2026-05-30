"""Needs API routes."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.need import Need
from app.schemas.need import NeedCreate, NeedRead, NeedUpdate
from app.services.need_service import (
    NeedNotFoundError,
    create_need,
    delete_need,
    get_need,
    list_needs,
    update_need,
)
from app.services.project_service import ProjectNotFoundError

router = APIRouter(tags=["needs"])


@router.get("/projects/{project_id}/needs", response_model=list[NeedRead])
async def list_need_route(project_id: int, db: Session = Depends(get_db)) -> list[Need]:
    """List needs under a project."""
    try:
        return list_needs(db, project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error


@router.post(
    "/projects/{project_id}/needs",
    response_model=NeedRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_need_route(
    payload: NeedCreate,
    project_id: int,
    db: Session = Depends(get_db),
) -> Need:
    """Create a need under a project."""
    try:
        return create_need(
            db,
            project_id,
            payload.statement,
            payload.context,
            payload.constraints,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error


@router.get("/needs/{need_id}", response_model=NeedRead)
async def get_need_route(need_id: int, db: Session = Depends(get_db)) -> Need:
    """Get a need."""
    try:
        return get_need(db, need_id)
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error


@router.patch("/needs/{need_id}", response_model=NeedRead)
async def update_need_route(
    payload: NeedUpdate,
    need_id: int,
    db: Session = Depends(get_db),
) -> Need:
    """Edit a need and clear its classification."""
    try:
        return update_need(
            db,
            need_id,
            payload.model_dump(exclude_unset=True),
        )
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error


@router.delete("/needs/{need_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_need_route(need_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a need."""
    try:
        delete_need(db, need_id)
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
