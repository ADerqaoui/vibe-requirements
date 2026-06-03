"""Specs API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.spec import Spec
from app.schemas.spec import SpecCreate, SpecOut, SpecTreeNode
from app.services.need_service import NeedNotFoundError
from app.services.layer_service import LayerNotAllowedForParentError, TargetLayerRequiredError
from app.services.spec_service import (
    SpecNotFoundError,
    create_spec_for_parent_spec,
    create_spec_for_need,
    latest_inspection_ids,
    list_full_spec_tree_for_need,
    list_children_of_spec,
    list_specs_for_need,
)

router = APIRouter(tags=["specs"])


@router.get("/needs/{need_id}/specs", response_model=list[SpecOut])
async def list_specs_route(need_id: int, db: Session = Depends(get_db)) -> list[SpecOut]:
    """List specs under a Need."""
    try:
        specs = list_specs_for_need(db, need_id)
        latest_ids = latest_inspection_ids(db, [spec.id for spec in specs])
        return [_spec_out(spec, latest_ids.get(spec.id)) for spec in specs]
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error


@router.get("/needs/{need_id}/spec-tree", response_model=list[SpecTreeNode])
async def list_spec_tree_route(need_id: int, db: Session = Depends(get_db)) -> list[SpecTreeNode]:
    """List the full nested Spec tree under a Need."""
    try:
        specs = list_full_spec_tree_for_need(db, need_id)
        latest_ids = latest_inspection_ids(db, [spec.id for spec in specs])
        return _spec_tree(specs, latest_ids)
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error


@router.post("/needs/{need_id}/specs", response_model=SpecOut, status_code=status.HTTP_201_CREATED)
async def create_spec_route(
    need_id: int,
    payload: SpecCreate,
    db: Session = Depends(get_db),
) -> SpecOut:
    """Create a spec under a Need."""
    try:
        return _spec_out(create_spec_for_need(db, need_id, payload.statement, payload.target_layer_id), None)
    except NeedNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need not found") from error
    except TargetLayerRequiredError:
        return _target_layer_required_response()
    except LayerNotAllowedForParentError as error:
        return _layer_not_allowed_response(error)


@router.get("/specs/{spec_id}/specs", response_model=list[SpecOut])
async def list_child_specs_route(spec_id: int, db: Session = Depends(get_db)) -> list[SpecOut]:
    """List direct child Specs under a Spec."""
    try:
        specs = list_children_of_spec(db, spec_id)
        latest_ids = latest_inspection_ids(db, [spec.id for spec in specs])
        return [_spec_out(spec, latest_ids.get(spec.id)) for spec in specs]
    except SpecNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found") from error


@router.post("/specs/{spec_id}/specs", response_model=SpecOut, status_code=status.HTTP_201_CREATED)
async def create_child_spec_route(
    spec_id: int,
    payload: SpecCreate,
    db: Session = Depends(get_db),
) -> SpecOut:
    """Create a child Spec under a Spec."""
    try:
        return _spec_out(create_spec_for_parent_spec(db, spec_id, payload.statement, payload.target_layer_id), None)
    except SpecNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spec not found") from error
    except TargetLayerRequiredError:
        return _target_layer_required_response()
    except LayerNotAllowedForParentError as error:
        return _layer_not_allowed_response(error)


def _spec_out(spec: Spec, latest_inspection_id: int | None) -> SpecOut:
    """Map ORM fields to the slice API shape."""
    return SpecOut(
        id=spec.id,
        need_id=spec.need_id,
        parent_spec_id=spec.parent_spec_id,
        layer_id=spec.layer_id,
        layer_name=_layer_name(spec),
        statement=spec.text,
        complexity=spec.complexity,
        status=spec.status,
        latest_inspection_id=latest_inspection_id,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
    )


def _spec_tree(specs: list[Spec], latest_ids: dict[int, int]) -> list[SpecTreeNode]:
    """Build a recursively nested Spec tree from id-ordered rows."""
    nodes = {
        spec.id: SpecTreeNode(
            id=spec.id,
            statement=spec.text,
            complexity=spec.complexity,
            status=spec.status,
            parent_spec_id=spec.parent_spec_id,
            layer_id=spec.layer_id,
            layer_name=_layer_name(spec),
            latest_inspection_id=latest_ids.get(spec.id),
            children=[],
        )
        for spec in specs
    }
    roots: list[SpecTreeNode] = []
    for spec in specs:
        node = nodes[spec.id]
        if spec.parent_spec_id is None:
            roots.append(node)
            continue
        parent = nodes.get(spec.parent_spec_id)
        if parent is not None:
            parent.children.append(node)
    return roots


def _layer_name(spec: Spec) -> str:
    """Return a display layer name for serialized specs."""
    layer = getattr(spec, "layer", None)
    return layer.name if layer is not None else ""


def _target_layer_required_response() -> JSONResponse:
    """Return the target-layer-required 422 body."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"error": "target_layer_required"},
    )


def _layer_not_allowed_response(error: LayerNotAllowedForParentError) -> JSONResponse:
    """Return the disallowed target layer 422 body."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": "layer_not_allowed_for_parent",
            "target_layer_id": error.target_layer_id,
            "allowed_layer_ids": error.allowed_layer_ids,
        },
    )
