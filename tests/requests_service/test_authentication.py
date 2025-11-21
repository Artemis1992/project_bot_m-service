"""Tests for API key authentication."""

import os
from unittest.mock import patch

import pytest
from django.test import RequestFactory
from rest_framework import exceptions

pytestmark = pytest.mark.django_db

from requests_app.authentication import APIKeyAuthentication


@pytest.fixture
def auth():
    return APIKeyAuthentication()


@pytest.fixture
def factory():
    return RequestFactory()


class TestAPIKeyAuthentication:
    def test_no_api_key_configured_allows_all(self, auth, factory):
        """When SERVICE_API_KEY is not set, allow all requests."""
        with patch.dict(os.environ, {}, clear=True):
            request = factory.get("/api/requests/")
            result = auth.authenticate(request)
            assert result is None

    def test_valid_api_key_succeeds(self, auth, factory):
        """Valid API key should authenticate successfully."""
        with patch.dict(os.environ, {"SERVICE_API_KEY": "test-key"}):
            request = factory.get("/api/requests/", HTTP_X_API_KEY="test-key")
            result = auth.authenticate(request)
            assert result is not None
            assert result[1] == "test-key"  # auth token

    def test_missing_api_key_raises_error(self, auth, factory):
        """Missing API key should raise AuthenticationFailed."""
        with patch.dict(os.environ, {"SERVICE_API_KEY": "test-key"}):
            request = factory.get("/api/requests/")
            with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
                auth.authenticate(request)
            assert "API key required" in str(exc_info.value)

    def test_invalid_api_key_raises_error(self, auth, factory):
        """Invalid API key should raise AuthenticationFailed."""
        with patch.dict(os.environ, {"SERVICE_API_KEY": "test-key"}):
            request = factory.get("/api/requests/", HTTP_X_API_KEY="wrong-key")
            with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
                auth.authenticate(request)
            assert "Invalid API key" in str(exc_info.value)

