"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("DJANGO_DEBUG", "true")
os.environ.setdefault("SERVICE_API_KEY", "test-api-key")
os.environ.setdefault("REPORTING_SERVICE_ENABLED", "false")
os.environ.setdefault("APPROVALS_SERVICE_ENABLED", "false")
os.environ.setdefault("NOTIFICATIONS_ENABLED", "false")

# Configure Django for tests
import django
from django.conf import settings

# Determine which service we're testing based on the test path
if "requests_service" in str(Path.cwd()) or "requests_service" in str(Path(__file__)):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_requests.settings")
elif "approvals_service" in str(Path.cwd()) or "approvals_service" in str(Path(__file__)):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "approvals_service.settings")
elif "categories_service" in str(Path.cwd()) or "categories_service" in str(Path(__file__)):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "categories_service.settings")

# Setup Django if settings module is set
if "DJANGO_SETTINGS_MODULE" in os.environ:
    django.setup()

# Pytest Django plugin configuration
import pytest

@pytest.fixture(scope="session")
def django_db_setup():
    """Setup Django database for tests."""
    pass

