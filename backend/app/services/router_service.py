"""Automatic model router service."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model import Model
from app.models.setting import Setting

ROUTER_ENABLED_KEY = "router_enabled"
TASK_TIER = {
    "generate_need_to_spec": "mid",
    "generate_spec_to_child": "mid",
    "inspect_spec": "high",
}
TIER_RANK = {"low": 0, "mid": 1, "high": 2}


class RouterNoModelError(Exception):
    """Raised when the router has no enabled model candidates."""


class RouterTaskNotRoutedError(Exception):
    """Raised when a task is outside router scope."""


def is_router_enabled(db: Session) -> bool:
    """Return true when the global router setting is enabled."""
    setting = db.get(Setting, ROUTER_ENABLED_KEY)
    if setting is None or setting.value is None:
        return False
    return setting.value.strip().lower() == "true"


def select_model(db: Session, task: str) -> Model:
    """Select one enabled model deterministically for a routed task."""
    if task not in TASK_TIER:
        raise RouterTaskNotRoutedError(f"Task is not routed: {task}")
    models = list(db.scalars(select(Model).where(Model.enabled == 1)).all())
    if not models:
        raise RouterNoModelError("No enabled models available for router")
    target_rank = TIER_RANK[TASK_TIER[task]]
    return min(models, key=lambda model: _ranking(model, target_rank))


def _ranking(model: Model, target_rank: int) -> tuple[int, int, float, int]:
    """Return the deterministic router ordering tuple."""
    tier_distance = abs(TIER_RANK[model.tier] - target_rank)
    free_rank = 0 if model.input_cost_per_1k == 0 and model.output_cost_per_1k == 0 else 1
    total_cost = model.input_cost_per_1k + model.output_cost_per_1k
    return (tier_distance, free_rank, total_cost, model.id)
