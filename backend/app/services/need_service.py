"""Need CRUD service."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.need import Need
from app.services.project_service import get_project


class NeedNotFoundError(Exception):
    """Raised when a need does not exist."""


def list_needs(db: Session, project_id: int) -> list[Need]:
    """Return all needs for a project in stable creation order."""
    get_project(db, project_id)
    statement = select(Need).where(Need.project_id == project_id).order_by(Need.id)
    return list(db.scalars(statement).all())


def create_need(
    db: Session,
    project_id: int,
    statement: str,
    context: str | None,
    constraints: str | None,
) -> Need:
    """Create a need under an existing project."""
    get_project(db, project_id)
    need = Need(
        project_id=project_id,
        statement=statement,
        context=context,
        constraints=constraints,
    )
    db.add(need)
    db.commit()
    db.refresh(need)
    return need


def get_need(db: Session, need_id: int) -> Need:
    """Return one need or raise if missing."""
    need = db.get(Need, need_id)
    if need is None:
        raise NeedNotFoundError
    return need


def update_need(
    db: Session,
    need_id: int,
    field_values: dict[str, str | None],
) -> Need:
    """Edit a need and clear its complexity classification."""
    need = get_need(db, need_id)
    for field_name, field_value in field_values.items():
        setattr(need, field_name, field_value)
    need.complexity = None
    need.updated_at = datetime.now(UTC).isoformat()
    db.commit()
    db.refresh(need)
    return need


def delete_need(db: Session, need_id: int) -> None:
    """Delete one need and let database cascades remove descendants."""
    need = get_need(db, need_id)
    db.delete(need)
    db.commit()
