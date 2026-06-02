from app.core.config import Settings
from app.services.balance_sync_service import BalanceSyncService


class FakeDollarQuoteSource:
    def __init__(self, quote: dict[str, object]) -> None:
        self._quote = quote

    def fetch_dollar_quote(self) -> dict[str, object]:
        return self._quote


class FakeDollarQuoteSink:
    def __init__(self, written_count: int | None = None) -> None:
        self.appended_quote: dict[str, object] | None = None
        self._written_count = written_count

    def append_dollar_quote(self, quote: dict[str, object]) -> int:
        self.appended_quote = quote
        return self._written_count if self._written_count is not None else 1


def test_run_in_dry_run_fetches_without_writing() -> None:
    settings = Settings(_env_file=None, DRY_RUN=True)
    sink = FakeDollarQuoteSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.fetched_count == 1
    assert summary.written_count == 0
    assert summary.dry_run is True
    assert sink.appended_quote is None


def test_run_writes_dollar_quote_when_dry_run_is_disabled() -> None:
    settings = Settings(
        _env_file=None,
        DRY_RUN=False,
        GOOGLE_APPLICATION_CREDENTIALS=__file__,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )
    quote = _dollar_quote()
    sink = FakeDollarQuoteSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(quote),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.fetched_count == 1
    assert summary.written_count == 1
    assert sink.appended_quote == quote


def test_run_uses_sink_written_count() -> None:
    settings = Settings(
        _env_file=None,
        DRY_RUN=False,
        GOOGLE_APPLICATION_CREDENTIALS=__file__,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )
    sink = FakeDollarQuoteSink(written_count=1)
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.written_count == 1


def _dollar_quote() -> dict[str, object]:
    return {
        "compra": 1410,
        "venta": 1430,
        "casa": "oficial",
        "nombre": "Oficial",
        "moneda": "USD",
        "fechaActualizacion": "2026-05-31T17:59:00Z",
    }
