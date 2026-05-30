"""Model registry API routes."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.model import Model
from app.schemas.model import ModelCreate, ModelRead, ModelUpdate
from app.services.model_service import (
    ModelHasCallHistoryError,
    ModelNotFoundError,
    create_model,
    delete_model,
    list_models,
    update_model,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelRead])
async def list_model_route(db: Session = Depends(get_db)) -> list[ModelRead]:
    """List models with cumulative cost."""
    return [_model_read(model, cost) for model, cost in list_models(db)]


@router.post("", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
async def create_model_route(payload: ModelCreate, db: Session = Depends(get_db)) -> ModelRead:
    """Create a model."""
    model = create_model(db, payload.model_dump())
    return _model_read(model, 0.0)


@router.patch("/{model_id}", response_model=ModelRead)
async def update_model_route(
    payload: ModelUpdate,
    model_id: int,
    db: Session = Depends(get_db),
) -> ModelRead:
    """Update a model."""
    try:
        model = update_model(db, model_id, payload.model_dump(exclude_unset=True))
    except ModelNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found") from error
    cost = next((model_cost for item, model_cost in list_models(db) if item.id == model.id), 0.0)
    return _model_read(model, cost)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_route(model_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a model."""
    try:
        delete_model(db, model_id)
    except ModelNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found") from error
    except ModelHasCallHistoryError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="model has call history; disable it instead",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _model_read(model: Model, cumulative_cost_sek: float) -> ModelRead:
    """Build a model response with computed cumulative cost."""
    return ModelRead(
        id=model.id,
        provider=model.provider,
        name=model.name,
        ollama_tag=model.ollama_tag,
        api_model_id=model.api_model_id,
        tier=model.tier,
        input_cost_per_1k=model.input_cost_per_1k,
        output_cost_per_1k=model.output_cost_per_1k,
        enabled=bool(model.enabled),
        cumulative_cost_sek=cumulative_cost_sek,
    )
