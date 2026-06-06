"""Global API error handler tests."""
import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_unexpected_exception_returns_structured_500_and_logs_traceback(
    caplog,
) -> None:
    """Unexpected route exceptions are structured and logged with traceback."""
    app = create_app()

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("unexpected boom")

    caplog.set_level(logging.ERROR)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/unexpected")

    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_error",
        "detail": "unexpected boom",
    }
    assert any("Unhandled exception" in record.message for record in caplog.records)
    assert any(record.exc_info for record in caplog.records)
