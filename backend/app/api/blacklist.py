"""Blacklist API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.schemas.blacklist import BlacklistCreate, BlacklistEntryOut
from app.services.blacklist_service import (
    BlacklistParentNotFoundError,
    BlacklistService,
    ParentKind,
    build_blacklist_service,
)
from app.services.embedding_service import EmbeddingError, EmbeddingService

router = APIRouter(tags=["blacklist"])


async def get_blacklist_service(db: Session = Depends(get_db)) -> BlacklistService:
    """Return the production blacklist service."""
    embedding_service = EmbeddingService(db, get_settings())
    return build_blacklist_service(db, embedding_service)


@router.post(
    "/needs/{need_id}/blacklist",
    response_model=BlacklistEntryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_need_blacklist_entry_route(
    need_id: int,
    payload: BlacklistCreate,
    service: BlacklistService = Depends(get_blacklist_service),
) -> BlacklistEntryOut:
    """Blacklist rejected text for a Need parent."""
    return await _create_blacklist_entry("need", need_id, payload, service)


@router.get("/needs/{need_id}/blacklist", response_model=list[BlacklistEntryOut])
async def list_need_blacklist_entries_route(
    need_id: int,
    service: BlacklistService = Depends(get_blacklist_service),
) -> list[BlacklistEntryOut]:
    """List blacklist entries for a Need parent."""
    return _list_blacklist_entries("need", need_id, service)


@router.post(
    "/specs/{spec_id}/blacklist",
    response_model=BlacklistEntryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_spec_blacklist_entry_route(
    spec_id: int,
    payload: BlacklistCreate,
    service: BlacklistService = Depends(get_blacklist_service),
) -> BlacklistEntryOut:
    """Blacklist rejected text for a Spec parent."""
    return await _create_blacklist_entry("spec", spec_id, payload, service)


@router.get("/specs/{spec_id}/blacklist", response_model=list[BlacklistEntryOut])
async def list_spec_blacklist_entries_route(
    spec_id: int,
    service: BlacklistService = Depends(get_blacklist_service),
) -> list[BlacklistEntryOut]:
    """List blacklist entries for a Spec parent."""
    return _list_blacklist_entries("spec", spec_id, service)


async def _create_blacklist_entry(
    parent_kind: ParentKind,
    parent_id: int,
    payload: BlacklistCreate,
    service: BlacklistService,
) -> BlacklistEntryOut:
    try:
        entry = await service.add_blacklist_entry(parent_kind, parent_id, payload.statement)
        return BlacklistEntryOut.model_validate(entry)
    except BlacklistParentNotFoundError as error:
        raise _not_found(parent_kind) from error
    except EmbeddingError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding failure: {error}",
        ) from error


def _list_blacklist_entries(
    parent_kind: ParentKind,
    parent_id: int,
    service: BlacklistService,
) -> list[BlacklistEntryOut]:
    try:
        return [
            BlacklistEntryOut.model_validate(entry)
            for entry in service.list_entries(parent_kind, parent_id)
        ]
    except BlacklistParentNotFoundError as error:
        raise _not_found(parent_kind) from error


def _not_found(parent_kind: ParentKind) -> HTTPException:
    detail = "Need not found" if parent_kind == "need" else "Spec not found"
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
