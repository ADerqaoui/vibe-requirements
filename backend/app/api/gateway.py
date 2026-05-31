"""Manual gateway API routes."""
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.gateway.base import Gateway, GatewayError
from app.gateway.factory import build_gateway
from app.models.model import Model
from app.schemas.completion import CompletionRequest, CompletionResult
from app.services.gateway_service import GatewayRuntime, complete_model
from app.services.model_service import ModelNotFoundError, get_model

router = APIRouter(prefix="/models", tags=["gateway"])
GatewayFactory = Callable[[Model, Settings], Gateway]


async def get_gateway_factory() -> GatewayFactory:
    """Return the production adapter factory."""
    return build_gateway


@router.post("/{model_id}/complete", response_model=CompletionResult)
async def complete_model_route(
    model_id: int,
    payload: CompletionRequest,
    db: Session = Depends(get_db),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
) -> CompletionResult:
    """Run a manual completion against an enabled model."""
    settings = get_settings()
    try:
        model = get_model(db, model_id)
    except ModelNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found") from error
    if not bool(model.enabled):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model is disabled")
    try:
        gateway = gateway_factory(model, settings)
        return await complete_model(
            db=db,
            model=model,
            gateway=gateway,
            prompt=payload.prompt,
            system=payload.system,
            runtime=GatewayRuntime(
                retry_count=settings.llm_retry_count,
                timeout_seconds=_timeout_for_provider(model.provider, settings),
            ),
        )
    except GatewayError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway failure: {error}",
        ) from error


def _timeout_for_provider(provider: str, settings: Settings) -> float:
    """Return provider-specific timeout."""
    if provider == "ollama":
        return settings.ollama_timeout_seconds
    return settings.cloud_timeout_seconds
