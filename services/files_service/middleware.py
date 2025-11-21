"""API Key middleware for FastAPI services."""

from __future__ import annotations

import os
from typing import Callable

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(request: Request, call_next: Callable):
    """
    Middleware to verify API key for inter-service communication.
    Skips authentication for health endpoints.
    """
    # Skip authentication for health checks
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("SERVICE_API_KEY")

    if not expected_key:
        # If no key is set, allow all (for development)
        return await call_next(request)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    return await call_next(request)

