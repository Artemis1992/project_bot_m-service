from __future__ import annotations

import datetime as dt
import os
import tempfile
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from modules.google_drive import GoogleDriveStorage
from modules.telegram_downloader import TelegramDownloader

app = FastAPI(title="files_service", version="0.1.0")

DOWNLOADER = TelegramDownloader(
    bot_token=os.getenv("BOT_TOKEN", "placeholder-token"),
)


def _load_service_account_json() -> str:
    """
    Reads service account either from a file path or JSON env variable.
    Returns an empty JSON object if nothing provided (stub mode).
    """
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as fp:
                return fp.read()
        except OSError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(f"Failed to read service account file: {exc}") from exc
    return os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")


STORAGE = GoogleDriveStorage(service_account_json=_load_service_account_json())


class TelegramFileRequest(BaseModel):
    telegram_file_id: str
    file_name: str = Field(min_length=1)
    warehouse: str
    category: str
    subcategory: str
    author_id: int


class FileUploadResponse(BaseModel):
    file_url: str
    storage_path: str
    file_name: str


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/files/from-telegram",
    response_model=FileUploadResponse,
    tags=["files"],
)
async def upload_from_telegram(payload: TelegramFileRequest) -> FileUploadResponse:
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            file_path = await DOWNLOADER.download_file(
                telegram_file_id=payload.telegram_file_id,
                destination_path=tmp_file.name,
            )
        storage_path = build_storage_path(
            category=payload.category,
            subcategory=payload.subcategory,
            filename=payload.file_name,
        )
        file_url = await STORAGE.upload(file_path, storage_path)
        return FileUploadResponse(
            file_url=file_url,
            storage_path=storage_path,
            file_name=payload.file_name,
        )
    except Exception as exc:  # pragma: no cover - placeholder for logging
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if "file_path" in locals():
            try:
                os.remove(file_path)
            except OSError:
                pass


def build_storage_path(category: str, subcategory: str, filename: str) -> str:
    normalized_category = category.replace(" ", "_")
    normalized_subcategory = subcategory.replace(" ", "_")
    now = dt.datetime.utcnow()
    unique_suffix = uuid.uuid4().hex[:8]
    return (
        f"/{normalized_category}/{normalized_subcategory}/"
        f"{now:%Y-%m}/{unique_suffix}_{filename}"
    )

