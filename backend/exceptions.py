"""APEX — Centralized Domain Exceptions and HTTP Handlers."""

import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ApexBaseException(Exception):
    """Base exception for all APEX domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(ApexBaseException):
    """Raised when an entity is not found in the database."""
    pass


class ProviderError(ApexBaseException):
    """Raised when an external data provider fails or returns invalid responses."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when an external provider throttles requests."""
    pass


class IngestionError(ApexBaseException):
    """Raised when the ingestion pipeline encounters an unrecoverable data conflict or validation error."""
    pass


class AuthenticationError(ApexBaseException):
    """Raised when authentication credentials or API keys are invalid."""
    pass


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        logger.warning(f"Entity not found: {exc.message} (Path: {request.url.path})")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "ENTITY_NOT_FOUND",
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(ProviderError)
    async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
        logger.error(f"Provider error: {exc.message} (Path: {request.url.path})")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": {
                    "code": "PROVIDER_ERROR",
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(ProviderRateLimitError)
    async def rate_limit_handler(request: Request, exc: ProviderRateLimitError) -> JSONResponse:
        logger.warning(f"Provider rate limit exceeded: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "PROVIDER_RATE_LIMIT",
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(IngestionError)
    async def ingestion_error_handler(request: Request, exc: IngestionError) -> JSONResponse:
        logger.error(f"Ingestion failed: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INGESTION_ERROR",
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        logger.warning(f"Unauthorized request: {exc.message} (Path: {request.url.path})")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info(f"Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters or payload",
                    "details": {"validation_errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled internal server error on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred",
                }
            },
        )
