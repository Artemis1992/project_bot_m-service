import asyncio

from sheets.connector import SheetsConnector
from sheets.writer import RequestsSheetWriter


def test_connector_append_row_in_dry_run_appends_locally() -> None:
    connector = SheetsConnector(spreadsheet_key="")
    row_id = asyncio.run(connector.append_row("Reports", [1, "goal"]))
    assert row_id == "dry-run!1"
    assert connector._dry_run_rows == [[1, "goal"]]  # noqa: SLF001


def test_writer_builds_row_and_calls_connector_in_dry_run() -> None:
    writer = RequestsSheetWriter(
        spreadsheet_key="",
        worksheet_name="Reports",
        service_account_file=None,
        service_account_json=None,
    )

    payload = {
        "request_id": 5,
        "goal": "test goal",
        "item_name": "item",
        "quantity": "2",
        "amount": 123.5,
        "comment": "note",
        "status": "approved",
        "history": "done",
    }

    row_id = asyncio.run(writer.append_request(payload))
    assert row_id == "dry-run!1"
    # при пустом spreadsheet_key коннектор работает в dry-run
    assert writer.connector._dry_run_rows == [  # noqa: SLF001
        [5, "test goal", "item", "2", 123.5, "note", "approved", "done"]
    ]
