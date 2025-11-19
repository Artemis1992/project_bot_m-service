from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from sheets.writer import RequestsSheetWriter

load_dotenv()

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_REPORTING_SHEET = os.getenv("GOOGLE_REPORTING_SHEET", "Reports")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

app = FastAPI(title="reporting_service", version="0.1.0")

writer = RequestsSheetWriter(
    spreadsheet_key=GOOGLE_SHEET_ID,
    worksheet_name=GOOGLE_REPORTING_SHEET,
    service_account_file=GOOGLE_SERVICE_ACCOUNT_FILE,
    service_account_json=GOOGLE_SERVICE_ACCOUNT_JSON,
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
