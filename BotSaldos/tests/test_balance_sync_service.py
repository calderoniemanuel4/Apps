from datetime import date
from decimal import Decimal

from app.core.config import Settings
from app.schemas.transaction import Transaction
from app.services.balance_sync_service import BalanceSyncService


class FakeTransactionSource:
    def __init__(self, transactions: list[dict[str, object]]) -> None:
        self._transactions = transactions

    def fetch_transactions(self) -> list[dict[str, object]]:
        return self._transactions


class FakeTransactionSink:
    def __init__(self) -> None:
        self.appended_transactions: list[Transaction] | None = None

    def append_transactions(self, transactions: list[Transaction]) -> None:
        self.appended_transactions = transactions


def test_run_in_dry_run_normalizes_without_writing() -> None:
    settings = Settings(_env_file=None, DRY_RUN=True)
    sink = FakeTransactionSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeTransactionSource([_raw_transaction(external_id="api-1")]),
        web_client=FakeTransactionSource([]),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.raw_count == 1
    assert summary.validated_count == 1
    assert summary.written_count == 0
    assert summary.dry_run is True
    assert sink.appended_transactions is None


def test_run_writes_valid_transactions_when_dry_run_is_disabled() -> None:
    settings = Settings(
        _env_file=None,
        DRY_RUN=False,
        GOOGLE_APPLICATION_CREDENTIALS=__file__,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )
    sink = FakeTransactionSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeTransactionSource([_raw_transaction(external_id="api-1")]),
        web_client=FakeTransactionSource([]),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.validated_count == 1
    assert summary.written_count == 1
    assert sink.appended_transactions is not None
    assert sink.appended_transactions[0].external_id == "api-1"


def test_run_skips_invalid_transactions_and_duplicate_external_ids() -> None:
    settings = Settings(_env_file=None, DRY_RUN=True)
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeTransactionSource(
            [
                _raw_transaction(external_id="same-id"),
                _raw_transaction(external_id="same-id"),
                {"description": ""},
            ]
        ),
        web_client=FakeTransactionSource([_raw_transaction(external_id=None)]),
        sheets_client=FakeTransactionSink(),
    )

    summary = service.run()

    assert summary.raw_count == 4
    assert summary.validated_count == 2
    assert summary.duplicate_count == 1
    assert summary.invalid_count == 1


def _raw_transaction(external_id: str | None) -> dict[str, object]:
    return {
        "occurred_on": date(2026, 5, 31),
        "description": "Movimiento de prueba",
        "amount": Decimal("1500.25"),
        "currency": "ARS",
        "transaction_type": "income",
        "source": "test",
        "external_id": external_id,
    }
