"""Generation API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.gateway import GatewayFactory, get_gateway_factory
from app.config import get_settings
from app.db import get_db
from app.generation.parser import ParseError
from app.gateway.base import GatewayError
from app.schemas.generation import GenerationRequest, GenerationResult
from app.services.generation_service import GenerationRuntime, generate_specs_for_need
from app.services.model_service import ModelNotFoundError, get_model
from app.services.need_service import NeedNotFoundError, get_need

router = APIRouter(prefix="/needs/{need_id}/generate", tags=["generations"])


@router.post("", response_model=GenerationResult)
async def generate_specs_route(
    need_id: int,
    payload: GenerationRequest,
    db: Session = Depends(get_db),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
) -> GenerationResult:
    """Generate child spec candidates from a Need."""
    settings = get_settings()
    try:
        need = get_need(db, need_id)
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error
    try:
        model = get_model(db, payload.model_id)
    except ModelNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model not found") from error
    if not bool(model.enabled):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model is disabled")

    try:
        gateway = gateway_factory(model, settings)
        return await generate_specs_for_need(
            db=db,
            need=need,
            model=model,
            gateway=gateway,
            count=payload.count,
            runtime=GenerationRuntime(
                retry_count=settings.llm_retry_count,
                timeout_seconds=_timeout_for_provider(model.provider, settings),
            ),
        )
    except ParseError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except GatewayError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway failure: {error}",
        ) from error


def _timeout_for_provider(provider: str, settings) -> float:
    """Return provider-specific timeout."""
    if provider == "ollama":
        return settings.ollama_timeout_seconds
    return settings.cloud_timeout_seconds
