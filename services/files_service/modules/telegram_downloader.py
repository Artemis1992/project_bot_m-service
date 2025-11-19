from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any


class TelegramDownloader:
    """
    Заглушка загрузчика файлов из Telegram.
    На бою сюда можно подключить aiogram Bot или HTTP API Telegram.
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    async def download_file(self, telegram_file_id: str, destination_path: str) -> str:
        # TODO: подключить реальную загрузку через Bot API
        await asyncio.sleep(0.01)  # имитация IO
        path = Path(destination_path)
        path.write_bytes(b"placeholder file content")
        return str(path)
