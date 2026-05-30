"""Projects API routes."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectRead, ProjectRename
from app.services.project_service import (
    DuplicateProjectNameError,
    ProjectNotFoundError,
    create_project,
    delete_project,
    get_project,
    list_projects,
    rename_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
async def list_project_route(db: Session = Depends(get_db)) -> list[Project]:
    """List projects."""
    return list_projects(db)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project_route(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    """Create a project."""
    try:
        return create_project(db, payload.name)
    except DuplicateProjectNameError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project name exists") from error


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project_route(project_id: int, db: Session = Depends(get_db)) -> ProjectDetail:
    """Get a project. Needs are out of scope for this slice."""
    try:
        project = get_project(db, project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error
    return ProjectDetail.model_validate(project).model_copy(update={"needs": []})


@router.patch("/{project_id}", response_model=ProjectRead)
async def rename_project_route(
    payload: ProjectRename,
    project_id: int,
    db: Session = Depends(get_db),
) -> Project:
    """Rename a project."""
    try:
        return rename_project(db, project_id, payload.name)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error
    except DuplicateProjectNameError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project name exists") from error


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_route(project_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a project."""
    try:
        delete_project(db, project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
