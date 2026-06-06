"""Shared API error mapping helpers."""
import logging

from fastapi import Request
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


async def unhandled_exception_response(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured response for unexpected exceptions."""
    logging.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "detail": str(exc)},
    )
