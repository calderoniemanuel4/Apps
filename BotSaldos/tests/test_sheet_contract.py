import json
from datetime import datetime, timezone

import pytest

from app.schemas.sheet_contract import (
    SheetContractError,
    USD_QUOTE_WORKSHEET_CONTRACT,
    USD_QUOTE_WORKSHEET_HEADERS,
    dollar_quote_to_sheet_row,
)
from app.schemas.transaction import BalanceStatus, MonetaryBalance


def test_usd_quote_worksheet_contract_accepts_expected_headers() -> None:
    USD_QUOTE_WORKSHEET_CONTRACT.validate_headers(list(USD_QUOTE_WORKSHEET_HEADERS))


def test_usd_quote_worksheet_contract_rejects_missing_header() -> None:
    headers = list(USD_QUOTE_WORKSHEET_HEADERS[:-1])

    with pytest.raises(SheetContractError, match="Encabezados invalidos"):
        USD_QUOTE_WORKSHEET_CONTRACT.validate_headers(headers)


def test_dollar_quote_to_sheet_row_includes_api_response() -> None:
    quote = {
        "compra": 1410,
        "venta": 1430,
        "casa": "oficial",
        "nombre": "Oficial",
        "moneda": "USD",
        "fechaActualizacion": "2026-05-31T17:59:00Z",
    }
    fetched_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    row = dollar_quote_to_sheet_row(quote, fetched_at=fetched_at)

    assert row == [
        "2026-06-02T12:00:00+00:00",
        "",
        "ARS",
        "skipped",
        "",
        "1410",
        "1430",
        "oficial",
        "Oficial",
        "USD",
        "2026-05-31T17:59:00Z",
        json.dumps(quote, ensure_ascii=True, sort_keys=True),
    ]


def test_dollar_quote_to_sheet_row_includes_santander_balance() -> None:
    quote = {"venta": 1430}
    balance = MonetaryBalance(
        amount="123456.78",
        currency="ARS",
        status=BalanceStatus.SUCCESS,
        source="santander",
    )
    fetched_at = datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc)

    row = dollar_quote_to_sheet_row(quote, santander_balance=balance, fetched_at=fetched_at)

    assert row[1:5] == ["123456.78", "ARS", "success", ""]
