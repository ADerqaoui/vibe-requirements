"""Shared prompt store query predicates."""
from sqlalchemy import and_, case, desc, select

from app.models.layer import Layer
from app.models.prompt import Prompt


def group_filter(task: str, layer_id: int | None):
    """Return the task/layer group predicate."""
    if layer_id is None:
        return and_(Prompt.task == task, Prompt.layer_id.is_(None))
    return and_(Prompt.task == task, Prompt.layer_id == layer_id)


def ordered_enabled():
    """Return enabled prompts in task and layer order."""
    return (
        select(Prompt)
        .outerjoin(Layer, Layer.id == Prompt.layer_id)
        .where(Prompt.enabled == 1)
        .order_by(Prompt.task, case((Prompt.layer_id.is_(None), 0), else_=1), Layer.sort_order, Prompt.layer_id)
    )


def ordered_task_versions(task: str):
    """Return all prompt versions for one task in stable display order."""
    return (
        select(Prompt)
        .outerjoin(Layer, Layer.id == Prompt.layer_id)
        .where(Prompt.task == task)
        .order_by(
            case((Prompt.layer_id.is_(None), 0), else_=1),
            Layer.sort_order,
            Prompt.layer_id,
            Prompt.name,
            desc(Prompt.version),
            desc(Prompt.id),
        )
    )
