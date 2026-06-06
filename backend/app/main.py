"""FastAPI application entry point."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import unhandled_exception_response
from app.api.blacklist import router as blacklist_router
from app.api.classification import router as classification_router
from app.api.cost import router as cost_router
from app.api.decisions import router as decisions_router
from app.api.export import router as export_router
from app.api.gateway import router as gateway_router
from app.api.generations import router as generations_router
from app.api.health import router as health_router
from app.api.inspections import router as inspections_router
from app.api.layers import router as layers_router
from app.api.models import router as models_router
from app.api.needs import router as needs_router
from app.api.projects import router as projects_router
from app.api.prompts import router as prompts_router
from app.api.settings import router as settings_router
from app.api.specs import router as specs_router
from app.bootstrap import run_startup_db_setup
from app.config import get_settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        run_startup_db_setup(settings)
        yield

    app = FastAPI(title="Requirement Review Dashboard", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(Exception, unhandled_exception_response)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(export_router, prefix="/api")
    app.include_router(needs_router, prefix="/api")
    app.include_router(generations_router, prefix="/api")
    app.include_router(blacklist_router, prefix="/api")
    app.include_router(specs_router, prefix="/api")
    app.include_router(inspections_router, prefix="/api")
    app.include_router(decisions_router, prefix="/api")
    app.include_router(classification_router, prefix="/api")
    app.include_router(layers_router, prefix="/api")
    app.include_router(models_router, prefix="/api")
    app.include_router(gateway_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(cost_router, prefix="/api")
    app.include_router(prompts_router, prefix="/api")
    return app


app = create_app()
