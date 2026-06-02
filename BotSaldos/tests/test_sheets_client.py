import json

import pytest

from app.core.config import Settings
from app.integrations.sheets_client import SheetsClient, SheetsClientError
from app.schemas.sheet_contract import USD_QUOTE_WORKSHEET_HEADERS


class FakeWorksheet:
    def __init__(
        self,
        headers: list[str],
        fail_on_append: bool = False,
    ) -> None:
        self._headers = headers
        self._fail_on_append = fail_on_append
        self.appended_rows: list[list[str]] | None = None

    def row_values(self, row: int) -> list[str]:
        assert row == 1
        return self._headers

    def append_rows(self, rows: list[list[str]], value_input_option: str) -> None:
        if self._fail_on_append:
            raise FakeGspreadError("api unavailable")
        self.appended_rows = rows
        self.value_input_option = value_input_option


class FakeGspreadError(Exception):
    pass


FakeGspreadError.__module__ = "gspread.exceptions"


class FakeSpreadsheet:
    def __init__(self, worksheet: FakeWorksheet) -> None:
        self._worksheet = worksheet
        self.requested_worksheet_name: str | None = None

    def worksheet(self, name: str) -> FakeWorksheet:
        self.requested_worksheet_name = name
        return self._worksheet


class FakeGspreadClient:
    def __init__(self, spreadsheet: FakeSpreadsheet) -> None:
        self._spreadsheet = spreadsheet
        self.requested_key: str | None = None

    def open_by_key(self, key: str) -> FakeSpreadsheet:
        self.requested_key = key
        return self._spreadsheet


def test_append_dollar_quote_validates_headers_and_appends_row() -> None:
    worksheet = FakeWorksheet(headers=list(USD_QUOTE_WORKSHEET_HEADERS))
    spreadsheet = FakeSpreadsheet(worksheet=worksheet)
    gspread_client = FakeGspreadClient(spreadsheet=spreadsheet)
    settings = Settings(_env_file=None, GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id")
    client = SheetsClient(settings=settings, gspread_client=gspread_client)
    quote = _dollar_quote()

    written_count = client.append_dollar_quote(quote)

    assert written_count == 1
    assert gspread_client.requested_key == "sheet-id"
    assert spreadsheet.requested_worksheet_name == "Cotizaciones"
    assert worksheet.value_input_option == "RAW"
    assert worksheet.appended_rows is not None
    row = worksheet.appended_rows[0]
    assert row[1:] == [
        "1410",
        "1430",
        "oficial",
        "Oficial",
        "USD",
        "2026-05-31T17:59:00Z",
        json.dumps(quote, ensure_ascii=True, sort_keys=True),
    ]


def test_append_dollar_quote_rejects_invalid_headers_before_writing() -> None:
    worksheet = FakeWorksheet(headers=["compra"])
    spreadsheet = FakeSpreadsheet(worksheet=worksheet)
    gspread_client = FakeGspreadClient(spreadsheet=spreadsheet)
    settings = Settings(_env_file=None, GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id")
    client = SheetsClient(settings=settings, gspread_client=gspread_client)

    with pytest.raises(ValueError, match="Encabezados invalidos"):
        client.append_dollar_quote(_dollar_quote())

    assert worksheet.appended_rows is None


def test_append_dollar_quote_wraps_gspread_errors() -> None:
    worksheet = FakeWorksheet(
        headers=list(USD_QUOTE_WORKSHEET_HEADERS),
        fail_on_append=True,
    )
    spreadsheet = FakeSpreadsheet(worksheet=worksheet)
    gspread_client = FakeGspreadClient(spreadsheet=spreadsheet)
    settings = Settings(_env_file=None, GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id")
    client = SheetsClient(settings=settings, gspread_client=gspread_client)

    with pytest.raises(SheetsClientError, match="Google Sheets"):
        client.append_dollar_quote(_dollar_quote())


def test_append_dollar_quote_requires_spreadsheet_id() -> None:
    settings = Settings(_env_file=None)
    client = SheetsClient(settings=settings, gspread_client=object())

    with pytest.raises(SheetsClientError, match="GOOGLE_SHEETS_SPREADSHEET_ID"):
        client.append_dollar_quote(_dollar_quote())


def _dollar_quote() -> dict[str, object]:
    return {
        "compra": 1410,
        "venta": 1430,
        "casa": "oficial",
        "nombre": "Oficial",
        "moneda": "USD",
        "fechaActualizacion": "2026-05-31T17:59:00Z",
    }
