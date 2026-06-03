"""V-model layer lookup service."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.layer_parent import LayerParent

NEED_LAYER_NAME = "Need"


class LayerNotFoundError(Exception):
    """Raised when a layer id is unknown."""


class LayerParentSelectorError(Exception):
    """Raised when allowed-child selector inputs are invalid."""


class LayerNotAllowedForParentError(Exception):
    """Raised when a target layer is not allowed for a parent."""

    def __init__(self, target_layer_id: int, allowed_layer_ids: list[int]) -> None:
        self.target_layer_id = target_layer_id
        self.allowed_layer_ids = allowed_layer_ids
        super().__init__("Layer is not allowed for parent")


class TargetLayerRequiredError(Exception):
    """Raised when no unambiguous target layer can be selected."""


def list_layers(db: Session) -> list[Layer]:
    """Return all V-model layers in display order."""
    return list(db.scalars(select(Layer).order_by(Layer.sort_order, Layer.id)).all())


def allowed_children_for_need(db: Session) -> list[Layer]:
    """Return layers allowed directly under a Need."""
    need_layer = db.scalar(select(Layer).where(Layer.name == NEED_LAYER_NAME).limit(1))
    if need_layer is None:
        raise LayerNotFoundError
    return allowed_children_for_layer(db, need_layer.id)


def allowed_children_for_layer(db: Session, parent_layer_id: int) -> list[Layer]:
    """Return layers allowed directly under the given parent layer."""
    if db.get(Layer, parent_layer_id) is None:
        raise LayerNotFoundError
    return list(
        db.scalars(
            select(Layer)
            .join(LayerParent, LayerParent.layer_id == Layer.id)
            .where(LayerParent.parent_layer_id == parent_layer_id)
            .order_by(Layer.sort_order, Layer.id)
        ).all()
    )


def resolve_target_layer_for_need(db: Session, target_layer_id: int | None) -> Layer:
    """Resolve and validate a Need child target layer."""
    return _resolve_target_layer(allowed_children_for_need(db), target_layer_id)


def resolve_target_layer_for_spec(db: Session, parent_layer_id: int, target_layer_id: int | None) -> Layer:
    """Resolve and validate a Spec child target layer."""
    return _resolve_target_layer(allowed_children_for_layer(db, parent_layer_id), target_layer_id)


def _resolve_target_layer(allowed_layers: list[Layer], target_layer_id: int | None) -> Layer:
    """Resolve an explicit target or default the only allowed child."""
    if target_layer_id is None:
        if len(allowed_layers) == 1:
            return allowed_layers[0]
        raise TargetLayerRequiredError
    for layer in allowed_layers:
        if layer.id == target_layer_id:
            return layer
    raise LayerNotAllowedForParentError(target_layer_id, [layer.id for layer in allowed_layers])
