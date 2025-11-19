from __future__ import annotations

import asyncio
from pathlib import Path


class GoogleDriveStorage:
    """
    Заглушка-адаптер для загрузки файлов в Google Drive / Shared Drive.
    Сейчас имитирует загрузку и возвращает предсказуемую ссылку. Перед
    реальным продом замените на вызовы Google Drive API.
    """

    def __init__(self, service_account_json: str):
        self.service_account_json = service_account_json

    async def upload(self, local_path: str, storage_path: str) -> str:
        await asyncio.sleep(0.01)  # псевдо-пауза имитации сети
        if not Path(local_path).exists():
            raise FileNotFoundError(local_path)
        return f"https://files.local{storage_path}"
