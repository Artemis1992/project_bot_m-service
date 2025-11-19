"""
Centralised Google Sheets configuration shared between services.

Use these settings to keep both categories_service ("Categories") and
reporting_service ("Reports") aligned with the same spreadsheet.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleSheetsConfig:
    spreadsheet_id: str
    categories_tab: str
    reporting_tab: str
    service_account_file: str | None
    service_account_json: str | None


GOOGLE_SHEETS_CONFIG = GoogleSheetsConfig(
    spreadsheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
    categories_tab=os.getenv("GOOGLE_CATEGORIES_SHEET", "Categories"),
    reporting_tab=os.getenv("GOOGLE_REPORTING_SHEET", "Reports"),
    service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
    service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"),
)
