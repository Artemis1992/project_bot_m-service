"""Centralized logging configuration."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict


def setup_logging(service_name: str) -> None:
    """
    Setup centralized logging configuration.

    Supports:
    - JSON format for structured logging (when LOG_FORMAT=json)
    - Standard format for human-readable logs
    - Log level from LOG_LEVEL env var (default: INFO)
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "standard")

    if log_format == "json":
        # JSON format for structured logging (useful for log aggregation)
        import json
        from datetime import datetime

        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                from datetime import timezone
                log_data: Dict[str, Any] = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "service": service_name,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                if hasattr(record, "request_id"):
                    log_data["request_id"] = record.request_id
                return json.dumps(log_data)

        formatter = JSONFormatter()
    else:
        # Standard human-readable format
        formatter = logging.Formatter(
            "[{asctime}] {levelname} [{service}] {name}: {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Set level for third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("gspread").setLevel(logging.WARNING)

