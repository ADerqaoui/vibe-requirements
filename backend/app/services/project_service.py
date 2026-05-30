"""Project CRUD service."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.project import Project


class DuplicateProjectNameError(Exception):
    """Raised when a project name already exists."""


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist."""


def list_projects(db: Session) -> list[Project]:
    """Return all projects in stable creation order."""
    return list(db.scalars(select(Project).order_by(Project.id)).all())


def create_project(db: Session, name: str) -> Project:
    """Create a project, rejecting duplicate names."""
    if _project_name_exists(db, name):
        raise DuplicateProjectNameError

    project = Project(name=name)
    db.add(project)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateProjectNameError from error
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Project:
    """Return one project or raise if missing."""
    project = db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError
    return project


def rename_project(db: Session, project_id: int, name: str) -> Project:
    """Rename a project, rejecting duplicate names."""
    project = get_project(db, project_id)
    if _project_name_exists(db, name, excluding_project_id=project_id):
        raise DuplicateProjectNameError

    project.name = name
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateProjectNameError from error
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> None:
    """Delete one project and let database cascades remove descendants."""
    project = get_project(db, project_id)
    db.delete(project)
    db.commit()


def _project_name_exists(
    db: Session,
    name: str,
    excluding_project_id: int | None = None,
) -> bool:
    """Return whether a project name exists."""
    statement = select(Project.id).where(Project.name == name)
    if excluding_project_id is not None:
        statement = statement.where(Project.id != excluding_project_id)
    return db.scalar(statement) is not None
