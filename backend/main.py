"""APEX — Formula 1 Intelligence Backend Application Entry Point."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1 import api_v1_router
from backend.config import get_settings
from backend.exceptions import register_exception_handlers
from backend.logging_config import setup_logging

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("apex.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown lifecycle."""
    logger.info(f"Starting APEX Backend in '{settings.ENVIRONMENT}' mode on {settings.API_HOST}:{settings.API_PORT}")
    yield
    logger.info("Shutting down APEX Backend.")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="APEX — Formula 1 Intelligence API",
        description=(
            "Rigorous, research-driven Formula 1 intelligence platform combining "
            "canonical sporting entities, multi-provider ingestion, and probabilistic forecasting."
        ),
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Centralized Exception Handling
    register_exception_handlers(app)

    # API Routers
    app.include_router(api_v1_router)

    return app


app = create_app()
