from datetime import date
from decimal import Decimal

import pytest

from app.schemas.sheet_contract import (
    SheetContractError,
    TRANSACTIONS_WORKSHEET_CONTRACT,
    TRANSACTIONS_WORKSHEET_HEADERS,
    transaction_to_sheet_row,
)
from app.schemas.transaction import Transaction, TransactionType


def test_transactions_worksheet_contract_accepts_expected_headers() -> None:
    TRANSACTIONS_WORKSHEET_CONTRACT.validate_headers(list(TRANSACTIONS_WORKSHEET_HEADERS))


def test_transactions_worksheet_contract_rejects_missing_header() -> None:
    headers = list(TRANSACTIONS_WORKSHEET_HEADERS[:-1])

    with pytest.raises(SheetContractError, match="Encabezados invalidos"):
        TRANSACTIONS_WORKSHEET_CONTRACT.validate_headers(headers)


def test_transaction_to_sheet_row_uses_stable_values() -> None:
    transaction = Transaction(
        occurred_on=date(2026, 5, 28),
        description="Pago proveedor",
        amount=Decimal("1200.50"),
        currency="ARS",
        transaction_type=TransactionType.EXPENSE,
        source="manual",
        external_id="provider-20260528",
    )

    row = transaction_to_sheet_row(transaction)

    assert row == [
        "2026-05-28",
        "Pago proveedor",
        "1200.5",
        "ARS",
        "expense",
        "manual",
        "provider-20260528",
    ]


def test_transaction_to_sheet_row_uses_empty_external_id_when_missing() -> None:
    transaction = Transaction(
        occurred_on=date(2026, 5, 28),
        description="Ingreso efectivo",
        amount=Decimal("1000.00"),
        transaction_type=TransactionType.INCOME,
        source="manual",
    )

    row = transaction_to_sheet_row(transaction)

    assert row[-1] == ""
    assert row[2] == "1000"
