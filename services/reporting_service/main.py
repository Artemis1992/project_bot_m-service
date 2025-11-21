from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Add config directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "config"))

from google_sheets import GOOGLE_SHEETS_CONFIG  # noqa: E402
from middleware import verify_api_key  # noqa: E402
from sheets.writer import RequestsSheetWriter  # noqa: E402

load_dotenv()

app = FastAPI(title="reporting_service", version="0.1.0")
app.middleware("http")(verify_api_key)

# Use unified config
config = GOOGLE_SHEETS_CONFIG
writer = RequestsSheetWriter(
    spreadsheet_key=config.spreadsheet_id,
    worksheet_name=config.reporting_tab,
    service_account_file=config.service_account_file,
    service_account_json=config.service_account_json,
)


class RequestReport(BaseModel):
    request_id: int
    goal: str | None = None
    item_name: str | None = None
    quantity: str | None = None
    amount: float
    comment: str | None = None
    status: str
    history: str | None = None


@app.get("/health", tags=["health"])
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/reports/requests", tags=["reports"])
async def append_request(report: RequestReport) -> Dict[str, Any]:
    try:
        row_id = await writer.append_request(report.model_dump())
        return {"detail": "Строка добавлена в Google Sheets.", "google_row_id": row_id}
    except Exception as exc:  # pragma: no cover - placeholder logging
        raise HTTPException(status_code=500, detail=str(exc)) from exc
