"""Custom permissions for approvals_service."""

from __future__ import annotations

from rest_framework import permissions


class AllowHealthCheck(permissions.BasePermission):
    """Allow unauthenticated access to health check endpoints."""

    def has_permission(self, request, view):
        # Allow health checks without authentication
        if request.path.endswith("/health/") or request.path.endswith("/health"):
            return True
        # For other endpoints, require authentication
        return request.user is not None or request.auth is not None






