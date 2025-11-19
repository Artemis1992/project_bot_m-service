from __future__ import annotations

import asyncio
import json
from typing import Any, List

import gspread


class SheetsConnector:
    """
    Async wrapper around gspread with a dry-run fallback for local tests.
    """

    def __init__(
        self,
        spreadsheet_key: str,
        *,
        service_account_file: str | None = None,
        service_account_json: str | None = None,
    ) -> None:
        self.spreadsheet_key = spreadsheet_key
        self.service_account_file = service_account_file
        self.service_account_json = service_account_json
        self._client: gspread.Client | None = None
        self._dry_run_rows: List[list[Any]] = []

    def _build_client(self) -> gspread.Client:
        if self._client:
            return self._client
        if self.service_account_file:
            self._client = gspread.service_account(filename=self.service_account_file)
        elif self.service_account_json:
            self._client = gspread.service_account_from_dict(
                json.loads(self.service_account_json)
            )
        else:
            self._client = gspread.service_account()
        return self._client

    async def append_row(self, worksheet: str, row: list[Any]) -> str:
        if not self.spreadsheet_key:
            self._dry_run_rows.append(row)
            return f"dry-run!{len(self._dry_run_rows)}"

        return await asyncio.to_thread(self._append_row_sync, worksheet, row)

    def _append_row_sync(self, worksheet: str, row: list[Any]) -> str:
        ws = (
            self._build_client()
            .open_by_key(self.spreadsheet_key)
            .worksheet(worksheet)
        )
        ws.append_row(row, value_input_option="USER_ENTERED")
        return f"{worksheet}!A{ws.row_count}"
