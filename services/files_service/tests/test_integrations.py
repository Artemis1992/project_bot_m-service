import asyncio
from pathlib import Path

from modules.google_drive import GoogleDriveStorage
from modules.s3 import S3Storage
from modules.telegram_downloader import TelegramDownloader


def test_telegram_downloader_creates_file(tmp_path) -> None:
    downloader = TelegramDownloader(bot_token="token")
    destination = tmp_path / "file.bin"
    path = asyncio.run(
        downloader.download_file("file_id", destination_path=str(destination))
    )
    assert path == str(destination)
    assert destination.exists()
    assert destination.read_bytes()


def test_google_drive_storage_upload_returns_url(tmp_path) -> None:
    storage = GoogleDriveStorage(service_account_json="{}")
    local = tmp_path / "doc.txt"
    local.write_text("content", encoding="utf-8")
    storage_path = "/reports/2025-01/doc.txt"

    url = asyncio.run(storage.upload(str(local), storage_path))

    assert url.endswith(storage_path)
    assert url.startswith("https://files.local")


def test_google_drive_storage_upload_raises_on_missing_file(tmp_path) -> None:
    storage = GoogleDriveStorage(service_account_json="{}")
    try:
        asyncio.run(
            storage.upload(str(tmp_path / "absent.txt"), "/reports/absent.txt")
        )
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_s3_storage_upload_returns_s3_uri() -> None:
    storage = S3Storage(bucket="bucket-name")
    result = asyncio.run(storage.upload("/tmp/file.txt", "/path/to/file.txt"))
    assert result == "s3://bucket-name/path/to/file.txt"
