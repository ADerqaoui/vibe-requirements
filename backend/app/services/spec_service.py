"""Spec CRUD service for accepted generated candidates."""
from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session

from app.models.need import Need
from app.models.spec import Spec
from app.models.spec_inspection import SpecInspection
from app.services.layer_service import resolve_target_layer_for_need, resolve_target_layer_for_spec
from app.services.need_service import NeedNotFoundError, get_need
from app.services.req_id_service import next_req_id


class SpecNotFoundError(Exception):
    """Raised when a parent Spec is unavailable."""


def list_specs_for_need(db: Session, need_id: int) -> list[Spec]:
    """Return specs directly under a Need."""
    get_need(db, need_id)
    statement = (
        select(Spec)
        .where(Spec.need_id == need_id, Spec.parent_spec_id.is_(None))
        .order_by(Spec.id)
    )
    return list(db.scalars(statement).all())


def list_full_spec_tree_for_need(db: Session, need_id: int) -> list[Spec]:
    """Return every Spec under a Need ordered for deterministic tree building."""
    get_need(db, need_id)
    statement = select(Spec).where(Spec.need_id == need_id).order_by(Spec.id)
    return list(db.scalars(statement).all())


def latest_inspection_ids(db: Session, spec_ids: list[int]) -> dict[int, int]:
    """Return the latest persisted inspection id for each Spec id."""
    if len(spec_ids) == 0:
        return {}
    rows = db.execute(
        select(SpecInspection.spec_id, SpecInspection.id)
        .where(SpecInspection.spec_id.in_(spec_ids))
        .order_by(SpecInspection.spec_id, desc(SpecInspection.created_at), desc(SpecInspection.id))
    ).all()
    latest_ids: dict[int, int] = {}
    for spec_id, inspection_id in rows:
        if spec_id not in latest_ids:
            latest_ids[spec_id] = inspection_id
    return latest_ids


def list_children_of_spec(db: Session, spec_id: int) -> list[Spec]:
    """Return direct child Specs under a Spec."""
    get_spec(db, spec_id)
    statement = select(Spec).where(Spec.parent_spec_id == spec_id).order_by(Spec.id)
    return list(db.scalars(statement).all())


def create_spec_for_need(
    db: Session,
    need_id: int,
    statement: str,
    target_layer_id: int | None = None,
    source: str = "ai",
    status: str = "pending",
) -> Spec:
    """Persist one generated child spec under a Need with pending lifecycle status."""
    spec_text = _normalize_spec_text(statement)
    need = get_need(db, need_id)
    layer = resolve_target_layer_for_need(db, target_layer_id)
    spec = Spec(
        need_id=need.id,
        parent_spec_id=None,
        layer_id=layer.id,
        text=spec_text,
        status=status,
        source=source,
        req_id=next_req_id(db, need.project_id, layer),
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def create_spec_for_parent_spec(
    db: Session,
    spec_id: int,
    statement: str,
    target_layer_id: int | None = None,
    source: str = "ai",
    status: str = "pending",
) -> Spec:
    """Persist one generated child Spec under another Spec."""
    spec_text = _normalize_spec_text(statement)
    parent = get_spec(db, spec_id)
    need = get_need(db, parent.need_id)
    layer = resolve_target_layer_for_spec(db, parent.layer_id, target_layer_id)
    spec = Spec(
        need_id=parent.need_id,
        parent_spec_id=parent.id,
        layer_id=layer.id,
        text=spec_text,
        status=status,
        source=source,
        req_id=next_req_id(db, need.project_id, layer),
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def get_spec(db: Session, spec_id: int) -> Spec:
    """Return a Spec or raise a not-found error."""
    spec = db.get(Spec, spec_id)
    if spec is None:
        raise SpecNotFoundError
    return spec


def update_spec_text(db: Session, spec_id: int, text_value: str) -> Spec:
    """Edit one Spec's text in place and mark it as manual source."""
    normalized_text = text_value.strip()
    if normalized_text == "":
        raise ValueError("Spec text must not be blank")
    spec = get_spec(db, spec_id)
    spec.text = normalized_text
    spec.source = "manual"
    spec.updated_at = db.scalar(select(text("datetime('now')")))
    db.commit()
    db.refresh(spec)
    return spec


def ensure_need_exists(db: Session, need_id: int) -> Need:
    """Expose Need existence check for API consistency."""
    try:
        return get_need(db, need_id)
    except NeedNotFoundError:
        raise


def _normalize_spec_text(statement: str) -> str:
    """Trim and reject blank Spec text."""
    normalized_statement = statement.strip()
    if normalized_statement == "":
        raise ValueError("Spec statement must not be blank")
    return normalized_statement
