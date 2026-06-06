"""Prompt API response helpers."""
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.layer import Layer
from app.models.prompt import Prompt
from app.schemas.prompt import PromptRead, PromptVersionRead
from app.services.layer_service import NEED_LAYER_NAME


def layer_names(db: Session, prompts: list[Prompt]) -> dict[int, str]:
    """Return layer display names for prompt rows."""
    layer_ids = sorted({prompt.layer_id for prompt in prompts if prompt.layer_id is not None})
    if not layer_ids:
        return {}
    layers = db.scalars(select(Layer).where(Layer.id.in_(layer_ids))).all()
    return {layer.id: layer.name for layer in layers}


def read_prompt(prompt: Prompt, names: dict[int, str]) -> PromptRead:
    """Build an active prompt response with layer name."""
    layer_name = names.get(prompt.layer_id) if prompt.layer_id is not None else None
    return PromptRead.model_validate(prompt).model_copy(update={"layer_name": layer_name})


def read_version(prompt: Prompt, names: dict[int, str]) -> PromptVersionRead:
    """Build a prompt version response with layer name."""
    layer_name = names.get(prompt.layer_id) if prompt.layer_id is not None else None
    return PromptVersionRead.model_validate(prompt).model_copy(update={"layer_name": layer_name})


def default_layer_id(variants: list[Prompt], layer_id: int | None) -> int | None:
    """Return the group whose default should be preselected."""
    if layer_id is not None and any(variant.layer_id == layer_id for variant in variants):
        return layer_id
    return None


def invalid_layer_response(db: Session, layer_id: int) -> JSONResponse | None:
    """Return a validation response when a layer id is not authorable."""
    layer = db.get(Layer, layer_id)
    if layer is None:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "prompt_layer_invalid", "reason": "Layer does not exist"},
        )
    if layer.name == NEED_LAYER_NAME:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "prompt_layer_invalid", "reason": "Need layer cannot have prompt variants"},
        )
    return None
