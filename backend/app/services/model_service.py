"""Model registry service."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.call_log import CallLog
from app.models.model import Model


class ModelNotFoundError(Exception):
    """Raised when a model does not exist."""


class ModelHasCallHistoryError(Exception):
    """Raised when a model has call logs and should be disabled instead."""


def list_models(db: Session) -> list[tuple[Model, float]]:
    """Return models with cumulative logged SEK cost."""
    cost_totals = (
        select(CallLog.model_id, func.coalesce(func.sum(CallLog.cost_sek), 0).label("cost"))
        .group_by(CallLog.model_id)
        .subquery()
    )
    rows = db.execute(
        select(Model, func.coalesce(cost_totals.c.cost, 0.0))
        .outerjoin(cost_totals, cost_totals.c.model_id == Model.id)
        .order_by(Model.id)
    ).all()
    return [(model, float(cost)) for model, cost in rows]


def create_model(db: Session, values: dict[str, object]) -> Model:
    """Create a model registry row."""
    model = Model(**_database_values(values))
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_model(db: Session, model_id: int, values: dict[str, object]) -> Model:
    """Update a model registry row."""
    model = get_model(db, model_id)
    for field_name, field_value in _database_values(values).items():
        setattr(model, field_name, field_value)
    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model_id: int) -> None:
    """Delete a model registry row."""
    model = get_model(db, model_id)
    has_call_history = db.scalar(
        select(CallLog.id).where(CallLog.model_id == model_id).limit(1)
    )
    if has_call_history is not None:
        raise ModelHasCallHistoryError
    db.delete(model)
    db.commit()


def get_model(db: Session, model_id: int) -> Model:
    """Return a model or raise if missing."""
    model = db.get(Model, model_id)
    if model is None:
        raise ModelNotFoundError
    return model


def _database_values(values: dict[str, object]) -> dict[str, object]:
    """Convert API values to DB-compatible values."""
    converted_values = dict(values)
    if "enabled" in converted_values and converted_values["enabled"] is not None:
        converted_values["enabled"] = 1 if converted_values["enabled"] else 0
    return converted_values
