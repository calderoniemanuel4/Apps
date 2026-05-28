from datetime import date
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.integrations.sheets_client import SheetsClient, SheetsClientError
from app.schemas.sheet_contract import TRANSACTIONS_WORKSHEET_HEADERS
from app.schemas.transaction import Transaction, TransactionType


class FakeWorksheet:
    def __init__(self, headers: list[str]) -> None:
        self._headers = headers
        self.appended_rows: list[list[str]] | None = None

    def row_values(self, row: int) -> list[str]:
        assert row == 1
        return self._headers

    def append_rows(self, rows: list[list[str]], value_input_option: str) -> None:
        self.appended_rows = rows
        self.value_input_option = value_input_option


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


def test_append_transactions_validates_headers_and_appends_rows() -> None:
    worksheet = FakeWorksheet(headers=list(TRANSACTIONS_WORKSHEET_HEADERS))
    spreadsheet = FakeSpreadsheet(worksheet=worksheet)
    gspread_client = FakeGspreadClient(spreadsheet=spreadsheet)
    settings = Settings(_env_file=None, GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id")
    client = SheetsClient(settings=settings, gspread_client=gspread_client)
    transaction = Transaction(
        occurred_on=date(2026, 5, 28),
        description="Ingreso",
        amount=Decimal("2500"),
        currency="ARS",
        transaction_type=TransactionType.INCOME,
        source="api",
        external_id="api-1",
    )

    client.append_transactions([transaction])

    assert gspread_client.requested_key == "sheet-id"
    assert spreadsheet.requested_worksheet_name == "Movimientos"
    assert worksheet.value_input_option == "RAW"
    assert worksheet.appended_rows == [
        ["2026-05-28", "Ingreso", "2500", "ARS", "income", "api", "api-1"]
    ]


def test_append_transactions_rejects_invalid_headers_before_writing() -> None:
    worksheet = FakeWorksheet(headers=["occurred_on"])
    spreadsheet = FakeSpreadsheet(worksheet=worksheet)
    gspread_client = FakeGspreadClient(spreadsheet=spreadsheet)
    settings = Settings(_env_file=None, GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id")
    client = SheetsClient(settings=settings, gspread_client=gspread_client)
    transaction = Transaction(
        occurred_on=date(2026, 5, 28),
        description="Gasto",
        amount=Decimal("50"),
        transaction_type=TransactionType.EXPENSE,
        source="web",
    )

    with pytest.raises(ValueError, match="Encabezados invalidos"):
        client.append_transactions([transaction])

    assert worksheet.appended_rows is None


def test_append_transactions_requires_spreadsheet_id() -> None:
    settings = Settings(_env_file=None)
    client = SheetsClient(settings=settings, gspread_client=object())
    transaction = Transaction(
        occurred_on=date(2026, 5, 28),
        description="Gasto",
        amount=Decimal("50"),
        transaction_type=TransactionType.EXPENSE,
        source="web",
    )

    with pytest.raises(SheetsClientError, match="GOOGLE_SHEETS_SPREADSHEET_ID"):
        client.append_transactions([transaction])
