"""HTTP utilities for inter-service communication."""

from __future__ import annotations

import os
from typing import Dict


def get_api_headers() -> Dict[str, str]:
    """Get headers with API key for inter-service requests."""
    api_key = os.getenv("SERVICE_API_KEY")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    return headers






