"""Prompt registry API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.layer import Layer
from app.models.prompt import Prompt
from app.schemas.prompt import PromptRead, PromptVersionCreate, PromptVersionRead
from app.services.prompt_errors import PromptNotFoundError, PromptTemplateInvalidError
from app.services.layer_service import NEED_LAYER_NAME
from app.services.prompt_service import create_version, list_active, list_versions, promote

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptRead])
async def list_prompts_route(db: Session = Depends(get_db)) -> list[PromptRead]:
    """Return currently active prompts."""
    prompts = list_active(db)
    layer_names = _layer_names(db, prompts)
    return [_read_prompt(prompt, layer_names) for prompt in prompts]


@router.get("/{task}/versions", response_model=list[PromptVersionRead])
async def list_prompt_versions_route(
    task: str,
    db: Session = Depends(get_db),
) -> list[PromptVersionRead]:
    """Return full version history for one prompt task."""
    try:
        prompts = list_versions(db, task)
    except PromptNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt task not found") from error
    layer_names = _layer_names(db, prompts)
    return [_read_version(prompt, layer_names) for prompt in prompts]


@router.post("/{task}/versions", response_model=PromptVersionRead)
async def create_prompt_version_route(
    task: str,
    payload: PromptVersionCreate,
    db: Session = Depends(get_db),
) -> PromptVersionRead | JSONResponse:
    """Create a new active immutable prompt version."""
    if payload.layer_id is not None:
        invalid_response = _invalid_layer_response(db, payload.layer_id)
        if invalid_response is not None:
            return invalid_response
    try:
        prompt = create_version(
            db,
            task,
            payload.template,
            layer_id=payload.layer_id,
            name=payload.name,
            description=payload.description,
        )
    except PromptTemplateInvalidError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "prompt_template_invalid", "reason": error.reason},
        )
    except PromptNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt task not found") from error
    return _read_version(prompt, _layer_names(db, [prompt]))


@router.post("/{prompt_id}/promote", response_model=PromptVersionRead)
async def promote_prompt_route(
    prompt_id: int,
    db: Session = Depends(get_db),
) -> PromptVersionRead:
    """Promote an existing prompt version."""
    try:
        prompt = promote(db, prompt_id)
    except PromptNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found") from error
    return _read_version(prompt, _layer_names(db, [prompt]))


def _layer_names(db: Session, prompts: list[Prompt]) -> dict[int, str]:
    """Return layer display names for prompt rows."""
    layer_ids = sorted({prompt.layer_id for prompt in prompts if prompt.layer_id is not None})
    if not layer_ids:
        return {}
    layers = db.scalars(select(Layer).where(Layer.id.in_(layer_ids))).all()
    return {layer.id: layer.name for layer in layers}


def _read_prompt(prompt: Prompt, layer_names: dict[int, str]) -> PromptRead:
    """Build an active prompt response with layer name."""
    layer_name = layer_names.get(prompt.layer_id) if prompt.layer_id is not None else None
    return PromptRead.model_validate(prompt).model_copy(update={"layer_name": layer_name})


def _read_version(prompt: Prompt, layer_names: dict[int, str]) -> PromptVersionRead:
    """Build a prompt version response with layer name."""
    layer_name = layer_names.get(prompt.layer_id) if prompt.layer_id is not None else None
    return PromptVersionRead.model_validate(prompt).model_copy(update={"layer_name": layer_name})


def _invalid_layer_response(db: Session, layer_id: int) -> JSONResponse | None:
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
