"""Prompt registry API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.prompt_api_helpers import (
    default_layer_id,
    invalid_layer_response,
    layer_names,
    read_prompt,
    read_version,
)
from app.api.prompt_preview import router as prompt_preview_router
from app.db import get_db
from app.schemas.prompt import (
    PromptDefaultSet,
    PromptRead,
    PromptVariantRead,
    PromptVersionCreate,
    PromptVersionRead,
)
from app.services.prompt_errors import PromptNotFoundError, PromptTemplateInvalidError
from app.services.prompt_service import (
    create_version,
    get_default_variant_name,
    list_active,
    list_variants,
    list_versions,
    promote,
    set_default,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])
router.include_router(prompt_preview_router)


@router.get("", response_model=list[PromptRead])
async def list_prompts_route(db: Session = Depends(get_db)) -> list[PromptRead]:
    """Return currently active prompts."""
    prompts = list_active(db)
    names = layer_names(db, prompts)
    return [read_prompt(prompt, names) for prompt in prompts]


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
    names = layer_names(db, prompts)
    return [read_version(prompt, names) for prompt in prompts]


@router.get("/{task}/variants", response_model=list[PromptVariantRead])
async def list_prompt_variants_route(
    task: str,
    layer_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[PromptVariantRead]:
    """Return enabled variants accepted for one requested prompt group."""
    variants = list_variants(db, task, layer_id)
    names = layer_names(db, variants)
    selected_layer_id = default_layer_id(variants, layer_id)
    default_name = get_default_variant_name(db, task, selected_layer_id)
    return [
        PromptVariantRead(
            name=variant.name,
            version=variant.version,
            template=variant.template,
            is_default=variant.layer_id == selected_layer_id and variant.name == default_name,
            prompt_id=variant.id,
            layer_id=variant.layer_id,
            layer_name=names.get(variant.layer_id) if variant.layer_id is not None else None,
            scope_label=names.get(variant.layer_id) if variant.layer_id is not None else "Global",
        )
        for variant in variants
    ]


@router.post("/{task}/versions", response_model=PromptVersionRead)
async def create_prompt_version_route(
    task: str,
    payload: PromptVersionCreate,
    db: Session = Depends(get_db),
) -> PromptVersionRead | JSONResponse:
    """Create a new active immutable prompt version."""
    if payload.layer_id is not None:
        invalid_response = invalid_layer_response(db, payload.layer_id)
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
    return read_version(prompt, layer_names(db, [prompt]))


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
    return read_version(prompt, layer_names(db, [prompt]))


@router.post("/set-default", response_model=PromptDefaultSet)
async def set_default_prompt_route(
    payload: PromptDefaultSet,
    db: Session = Depends(get_db),
) -> PromptDefaultSet:
    """Set one task/layer default prompt variant."""
    try:
        set_default(db, payload.task, payload.layer_id, payload.name)
    except PromptNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt variant not found") from error
    return payload
