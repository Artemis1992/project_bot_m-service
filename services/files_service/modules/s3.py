from __future__ import annotations

import asyncio


class S3Storage:
    """Заглушка для S3-хранилища."""

    def __init__(self, bucket: str):
        self.bucket = bucket

    async def upload(self, local_path: str, storage_path: str) -> str:
        await asyncio.sleep(0.01)
        return f"s3://{self.bucket}{storage_path}"
