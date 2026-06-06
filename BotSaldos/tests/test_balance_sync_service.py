from pathlib import Path

from app.core.config import Settings
from app.core.login_attempt_state import LoginAttemptState
from app.integrations.balance_portal import SantanderClientError, SantanderFailureReason
from app.integrations.santander_selenium_client import SantanderSeleniumClient
from app.schemas.transaction import BalanceStatus, MonetaryBalance
from app.services.balance_sync_service import BalanceSyncService, _build_santander_client


class FakeDollarQuoteSource:
    def __init__(self, quote: dict[str, object]) -> None:
        self._quote = quote

    def fetch_dollar_quote(self) -> dict[str, object]:
        return self._quote


class FakeSantanderSource:
    def __init__(
        self,
        balance: MonetaryBalance | None = None,
        error: SantanderClientError | None = None,
    ) -> None:
        self._balance = balance
        self._error = error
        self.calls = 0

    def fetch_balance(self) -> MonetaryBalance:
        self.calls += 1
        if self._error is not None:
            raise self._error
        assert self._balance is not None
        return self._balance


class FakeDollarQuoteSink:
    def __init__(self, written_count: int | None = None) -> None:
        self.appended_quote: dict[str, object] | None = None
        self.appended_balance: MonetaryBalance | None = None
        self._written_count = written_count

    def append_dollar_quote(
        self,
        quote: dict[str, object],
        santander_balance: MonetaryBalance | None = None,
    ) -> int:
        self.appended_quote = quote
        self.appended_balance = santander_balance
        return self._written_count if self._written_count is not None else 1


def test_run_in_dry_run_fetches_api_without_writing() -> None:
    settings = Settings(_env_file=None, DRY_RUN=True)
    sink = FakeDollarQuoteSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        santander_client=FakeSantanderSource(),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.fetched_count == 1
    assert summary.written_count == 0
    assert summary.dry_run is True
    assert summary.santander_status == BalanceStatus.SKIPPED
    assert sink.appended_quote is None


def test_run_writes_dollar_quote_and_santander_balance(tmp_path: Path) -> None:
    settings = _settings_for_real_write(tmp_path, SANTANDER_ENABLED=True)
    quote = _dollar_quote()
    balance = MonetaryBalance(amount="1234.56", status=BalanceStatus.SUCCESS)
    sink = FakeDollarQuoteSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(quote),
        santander_client=FakeSantanderSource(balance=balance),
        sheets_client=sink,
        santander_attempt_state=_attempt_state(tmp_path),
    )

    summary = service.run()

    assert summary.written_count == 1
    assert summary.santander_status == BalanceStatus.SUCCESS
    assert sink.appended_quote == quote
    assert sink.appended_balance == balance


def test_run_records_santander_failure_and_continues_with_api(tmp_path: Path) -> None:
    settings = _settings_for_real_write(tmp_path, SANTANDER_ENABLED=True)
    state = _attempt_state(tmp_path)
    sink = FakeDollarQuoteSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        santander_client=FakeSantanderSource(
            error=SantanderClientError(
                SantanderFailureReason.INCORRECT_PASSWORD,
                "bad credentials",
            )
        ),
        sheets_client=sink,
        santander_attempt_state=state,
    )

    summary = service.run()

    assert summary.written_count == 1
    assert summary.santander_status == BalanceStatus.FAILED
    assert summary.santander_failure_reason == "incorrect_password"
    assert state.snapshot().failed_attempts == 1
    assert sink.appended_quote == _dollar_quote()


def test_run_does_not_count_balance_xpath_failure_as_login_attempt(tmp_path: Path) -> None:
    settings = _settings_for_real_write(tmp_path, SANTANDER_ENABLED=True)
    state = _attempt_state(tmp_path)
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        santander_client=FakeSantanderSource(
            error=SantanderClientError(
                SantanderFailureReason.BALANCE_NOT_FOUND,
                "missing xpath",
            )
        ),
        sheets_client=FakeDollarQuoteSink(),
        santander_attempt_state=state,
    )

    summary = service.run()

    assert summary.santander_status == BalanceStatus.FAILED
    assert summary.santander_failure_reason == "balance_not_found"
    assert state.snapshot().failed_attempts == 0


def test_run_skips_santander_when_attempt_limit_is_reached(tmp_path: Path) -> None:
    settings = _settings_for_real_write(tmp_path, SANTANDER_ENABLED=True)
    state = _attempt_state(tmp_path)
    state.record_failure("incorrect_password")
    state.record_failure("incorrect_password")
    santander = FakeSantanderSource(balance=MonetaryBalance(status=BalanceStatus.SUCCESS))
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        santander_client=santander,
        sheets_client=FakeDollarQuoteSink(),
        santander_attempt_state=state,
    )

    summary = service.run()

    assert summary.santander_status == BalanceStatus.BLOCKED
    assert summary.santander_failure_reason == "incorrect_password"
    assert santander.calls == 0


def test_build_santander_client_uses_selenium(tmp_path: Path) -> None:
    settings = _settings_for_real_write(
        tmp_path,
        SANTANDER_ENABLED=True,
    )

    assert isinstance(_build_santander_client(settings), SantanderSeleniumClient)


def _settings_for_real_write(tmp_path: Path, **overrides: object) -> Settings:
    credentials = tmp_path / "service-account.json"
    credentials.write_text("{}", encoding="utf-8")
    values: dict[str, object] = {
        "_env_file": None,
        "DRY_RUN": False,
        "GOOGLE_APPLICATION_CREDENTIALS": credentials,
        "GOOGLE_SHEETS_SPREADSHEET_ID": "sheet-id",
        "SANTANDER_USERNAME": "user",
        "SANTANDER_PASSWORD": "password",
        "SANTANDER_USERNAME_SELECTOR": "#user",
        "SANTANDER_PASSWORD_SELECTOR": "#password",
        "SANTANDER_SUBMIT_SELECTOR": "#submit",
        "SANTANDER_BALANCE_XPATH": "//saldo",
        "SANTANDER_LOGOUT_SELECTOR": "#logout",
        "SANTANDER_LOGOUT_CONFIRM_SELECTOR": "#confirm",
    }
    values.update(overrides)
    return Settings(**values)


def _attempt_state(tmp_path: Path) -> LoginAttemptState:
    return LoginAttemptState(path=tmp_path / "attempts.json", max_attempts=2)


def _dollar_quote() -> dict[str, object]:
    return {
        "compra": 1410,
        "venta": 1430,
        "casa": "oficial",
        "nombre": "Oficial",
        "moneda": "USD",
        "fechaActualizacion": "2026-05-31T17:59:00Z",
    }
