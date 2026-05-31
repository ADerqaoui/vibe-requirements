"""Spec CRUD service for accepted generated candidates."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.need import Need
from app.models.spec import Spec
from app.services.need_service import NeedNotFoundError, get_need

DEFAULT_SPEC_LAYER = "System Requirement"


class SpecLayerNotFoundError(Exception):
    """Raised when the default accepted spec layer is unavailable."""


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


def list_children_of_spec(db: Session, spec_id: int) -> list[Spec]:
    """Return direct child Specs under a Spec."""
    get_spec(db, spec_id)
    statement = select(Spec).where(Spec.parent_spec_id == spec_id).order_by(Spec.id)
    return list(db.scalars(statement).all())


def create_spec_for_need(db: Session, need_id: int, statement: str) -> Spec:
    """Persist one generated child spec under a Need with pending lifecycle status."""
    need = get_need(db, need_id)
    layer = _default_spec_layer(db)
    spec = Spec(
        need_id=need.id,
        parent_spec_id=None,
        layer_id=layer.id,
        text=statement,
        status="pending",
        source="ai",
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def create_spec_for_parent_spec(db: Session, spec_id: int, statement: str) -> Spec:
    """Persist one generated child Spec under another Spec."""
    parent = get_spec(db, spec_id)
    layer = _default_spec_layer(db)
    spec = Spec(
        need_id=parent.need_id,
        parent_spec_id=parent.id,
        layer_id=layer.id,
        text=statement,
        status="pending",
        source="ai",
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


def _default_spec_layer(db: Session) -> Layer:
    """Return the default Need child spec layer."""
    layer = db.scalar(select(Layer).where(Layer.name == DEFAULT_SPEC_LAYER).limit(1))
    if layer is None:
        raise SpecLayerNotFoundError
    return layer


def ensure_need_exists(db: Session, need_id: int) -> Need:
    """Expose Need existence check for API consistency."""
    try:
        return get_need(db, need_id)
    except NeedNotFoundError:
        raise
