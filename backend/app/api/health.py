"""Health check endpoint: reports DB and Ollama reachability."""
import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.db import engine

OLLAMA_TIMEOUT_S = 3.0

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Report overall status plus database and Ollama checks."""
    return {
        "status": "ok",
        "database": _check_database(),
        "ollama": await _check_ollama(),
    }


def _check_database() -> str:
    """Return 'ok' if a trivial query succeeds, else 'error'."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:  # noqa: BLE001
        return "error"


async def _check_ollama() -> str:
    """Return 'ok' if Ollama responds, else 'unreachable'."""
    url = f"{get_settings().ollama_host}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_S) as client:
            response = await client.get(url)
            response.raise_for_status()
        return "ok"
    except Exception:  # noqa: BLE001
        return "unreachable"
