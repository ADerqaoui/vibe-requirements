"""Spec classification API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.errors import cost_ceiling_response
from app.api.gateway import GatewayFactory, get_gateway_factory
from app.config import get_settings
from app.db import get_db
from app.gateway.base import CostCeilingExceededError, GatewayError
from app.models.spec import Spec
from app.schemas.classification import ClassificationResult
from app.services.classification_service import (
    ClassificationModelError,
    ClassificationParseError,
    ClassificationRuntime,
    classify_spec_complexity,
)

router = APIRouter(prefix="/specs", tags=["classification"])


@router.post("/{spec_id}/classify", response_model=ClassificationResult)
async def classify_spec_route(
    spec_id: int,
    db: Session = Depends(get_db),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
) -> ClassificationResult:
    """Classify a Spec's complexity."""
    spec = db.get(Spec, spec_id)
    if spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found")
    settings = get_settings()
    try:
        return await classify_spec_complexity(
            db=db,
            spec=spec,
            gateway_factory=gateway_factory,
            settings=settings,
            runtime=ClassificationRuntime(
                retry_count=settings.llm_retry_count,
                timeout_seconds=settings.ollama_timeout_seconds,
            ),
        )
    except ClassificationModelError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ClassificationParseError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    except CostCeilingExceededError as error:
        return cost_ceiling_response(error)
    except GatewayError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway failure: {error}",
        ) from error
