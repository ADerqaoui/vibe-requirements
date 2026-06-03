"""Prompt registry API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.prompt import PromptRead, PromptVersionCreate, PromptVersionRead
from app.services.prompt_errors import PromptNotFoundError, PromptTemplateInvalidError
from app.services.prompt_service import create_version, list_active, list_versions, promote

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptRead])
async def list_prompts_route(db: Session = Depends(get_db)) -> list[PromptRead]:
    """Return currently active prompts."""
    return [PromptRead.model_validate(prompt) for prompt in list_active(db)]


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
    return [PromptVersionRead.model_validate(prompt) for prompt in prompts]


@router.post("/{task}/versions", response_model=PromptVersionRead)
async def create_prompt_version_route(
    task: str,
    payload: PromptVersionCreate,
    db: Session = Depends(get_db),
) -> PromptVersionRead | JSONResponse:
    """Create a new active immutable prompt version."""
    try:
        prompt = create_version(
            db,
            task,
            payload.template,
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
    return PromptVersionRead.model_validate(prompt)


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
    return PromptVersionRead.model_validate(prompt)
