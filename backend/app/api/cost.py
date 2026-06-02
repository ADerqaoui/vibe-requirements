"""Cost summary API route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.cost import CostSummary
from app.services.cost_service import cost_summary

router = APIRouter(prefix="/cost-summary", tags=["cost"])


@router.get("", response_model=CostSummary)
async def cost_summary_route(db: Session = Depends(get_db)) -> CostSummary:
    """Return current cost ceiling and spend summary."""
    return cost_summary(db)
