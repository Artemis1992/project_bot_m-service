"""API Key authentication for inter-service communication."""

from __future__ import annotations

import os
from typing import Any

from rest_framework import authentication, exceptions


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Simple API key authentication for inter-service communication.
    Checks X-API-Key header against SERVICE_API_KEY env variable.
    """

    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_API_KEY")
        expected_key = os.getenv("SERVICE_API_KEY")

        if not expected_key:
            # If no key is set, allow all (for development)
            return None

        if not api_key:
            raise exceptions.AuthenticationFailed("API key required. Provide X-API-Key header.")

        if api_key != expected_key:
            raise exceptions.AuthenticationFailed("Invalid API key.")

        # Return a tuple of (user, auth). Since we don't have users, return None for user.
        return (None, api_key)






