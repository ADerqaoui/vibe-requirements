"""Layer API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.layer import LayerOut
from app.services.layer_service import (
    LayerNotFoundError,
    allowed_children_for_layer,
    allowed_children_for_need,
    list_layers,
)

router = APIRouter(tags=["layers"])


@router.get("/layers", response_model=list[LayerOut])
async def list_layers_route(db: Session = Depends(get_db)) -> list[LayerOut]:
    """List all V-model layers."""
    return list_layers(db)


@router.get("/layers/allowed-children", response_model=list[LayerOut])
async def allowed_children_route(
    parent_kind: str | None = Query(default=None),
    parent_layer_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[LayerOut]:
    """List layers allowed under a Need root or parent layer."""
    if (parent_kind is None) == (parent_layer_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one of parent_kind or parent_layer_id",
        )
    if parent_kind is not None:
        if parent_kind != "need":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown parent_kind")
        return allowed_children_for_need(db)
    try:
        return allowed_children_for_layer(db, parent_layer_id or 0)
    except LayerNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found") from error
