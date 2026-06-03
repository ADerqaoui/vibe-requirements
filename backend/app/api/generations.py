"""Generation API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.blacklist import get_blacklist_service
from app.api.errors import cost_ceiling_response
from app.api.gateway import GatewayFactory, get_gateway_factory
from app.config import get_settings
from app.db import get_db
from app.generation.parser import ParseError
from app.gateway.base import CostCeilingExceededError, GatewayError
from app.models.need import Need
from app.models.spec import Spec
from app.schemas.generation import GenerationRequest, GenerationResult
from app.services.blacklist_service import BlacklistService
from app.services.embedding_service import EmbeddingError
from app.services.generation_service import (
    GenerationParentNotFoundError,
    GenerationRuntime,
    ParentKind,
    generate_for_parent,
)
from app.services.layer_service import LayerNotAllowedForParentError, TargetLayerRequiredError
from app.services.model_service import ModelNotFoundError, get_model

router = APIRouter(tags=["generations"])


@router.post("/needs/{need_id}/generate", response_model=GenerationResult)
async def generate_specs_route(
    need_id: int,
    payload: GenerationRequest,
    db: Session = Depends(get_db),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
    blacklist_service: BlacklistService = Depends(get_blacklist_service),
) -> GenerationResult:
    """Generate child spec candidates from a Need."""
    return await _generate_specs_for_parent(
        "need",
        need_id,
        payload,
        db,
        gateway_factory,
        blacklist_service,
    )


@router.post("/specs/{spec_id}/generate", response_model=GenerationResult)
async def generate_child_specs_route(
    spec_id: int,
    payload: GenerationRequest,
    db: Session = Depends(get_db),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
    blacklist_service: BlacklistService = Depends(get_blacklist_service),
) -> GenerationResult:
    """Generate child spec candidates from a Spec."""
    return await _generate_specs_for_parent(
        "spec",
        spec_id,
        payload,
        db,
        gateway_factory,
        blacklist_service,
    )


async def _generate_specs_for_parent(
    parent_kind: ParentKind,
    parent_id: int,
    payload: GenerationRequest,
    db: Session,
    gateway_factory: GatewayFactory,
    blacklist_service: BlacklistService,
) -> GenerationResult:
    """Generate child spec candidates for either parent route."""
    settings = get_settings()
    _ensure_parent_exists(db, parent_kind, parent_id)
    try:
        model = get_model(db, payload.model_id)
    except ModelNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model not found") from error
    if not bool(model.enabled):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model is disabled")

    try:
        gateway = gateway_factory(model, settings)
        return await generate_for_parent(
            db=db,
            parent_kind=parent_kind,
            parent_id=parent_id,
            model=model,
            gateway=gateway,
            count=payload.count,
            runtime=GenerationRuntime(
                retry_count=settings.llm_retry_count,
                timeout_seconds=_timeout_for_provider(model.provider, settings),
            ),
            target_layer_id=payload.target_layer_id,
            blacklist_service=blacklist_service,
        )
    except GenerationParentNotFoundError as error:
        detail = "Need not found" if parent_kind == "need" else "Spec not found"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from error
    except ParseError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except TargetLayerRequiredError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"error": "target_layer_required"},
        )
    except LayerNotAllowedForParentError as error:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "layer_not_allowed_for_parent",
                "target_layer_id": error.target_layer_id,
                "allowed_layer_ids": error.allowed_layer_ids,
            },
        )
    except CostCeilingExceededError as error:
        return cost_ceiling_response(error)
    except GatewayError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway failure: {error}",
        ) from error
    except EmbeddingError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding failure: {error}",
        ) from error


def _timeout_for_provider(provider: str, settings) -> float:
    """Return provider-specific timeout."""
    if provider == "ollama":
        return settings.ollama_timeout_seconds
    return settings.cloud_timeout_seconds


def _ensure_parent_exists(db: Session, parent_kind: ParentKind, parent_id: int) -> None:
    """Raise a route-level 404 before model or gateway checks."""
    model_class = Need if parent_kind == "need" else Spec
    if db.get(model_class, parent_id) is None:
        detail = "Need not found" if parent_kind == "need" else "Spec not found"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
