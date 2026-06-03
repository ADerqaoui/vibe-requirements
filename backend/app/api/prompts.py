"""Read-only prompt registry API route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.prompt import PromptRead
from app.services.prompt_service import list_active

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptRead])
async def list_prompts_route(db: Session = Depends(get_db)) -> list[PromptRead]:
    """Return currently active prompts."""
    return [PromptRead.model_validate(prompt) for prompt in list_active(db)]
