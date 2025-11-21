"""Monitoring and health check utilities."""

from __future__ import annotations

import time
from typing import Any, Dict

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def health_check(request) -> JsonResponse:
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response with service status
    """
    return JsonResponse(
        {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "requests_service",
        }
    )


@require_http_methods(["GET"])
def readiness_check(request) -> JsonResponse:
    """
    Readiness check endpoint (checks database connectivity).

    Returns:
        JSON response with readiness status
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse(
            {
                "status": "ready",
                "timestamp": time.time(),
                "service": "requests_service",
            }
        )
    except Exception as exc:
        return JsonResponse(
            {
                "status": "not_ready",
                "error": str(exc),
                "timestamp": time.time(),
                "service": "requests_service",
            },
            status=503,
        )



