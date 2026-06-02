"""Shared API error mapping helpers."""
from fastapi import status
from fastapi.responses import JSONResponse

from app.gateway.base import CostCeilingExceededError


def cost_ceiling_response(error: CostCeilingExceededError) -> JSONResponse:
    """Return the structured cost-ceiling response."""
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={
            "error": "cost_ceiling_exceeded",
            "spent_sek": error.spent_sek,
            "ceiling_sek": error.ceiling_sek,
            "currency": "SEK",
        },
    )
