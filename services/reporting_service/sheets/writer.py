from __future__ import annotations

from typing import Any, Dict, List

from .connector import SheetsConnector


class RequestsSheetWriter:
    def __init__(
        self,
        spreadsheet_key: str,
        worksheet_name: str,
        *,
        service_account_file: str | None = None,
        service_account_json: str | None = None,
    ):
        self.connector = SheetsConnector(
            spreadsheet_key,
            service_account_file=service_account_file,
            service_account_json=service_account_json,
        )
        self.worksheet_name = worksheet_name

    async def append_request(self, payload: Dict[str, Any]) -> str:
        row = self._build_row(payload)
        return await self.connector.append_row(self.worksheet_name, row)

    def _build_row(self, payload: Dict[str, Any]) -> List[Any]:
        return [
            payload.get("request_id"),
            payload.get("goal"),
            payload.get("item_name"),
            payload.get("quantity"),
            payload.get("amount"),
            payload.get("comment"),
            payload.get("status"),
            payload.get("history"),
        ]
