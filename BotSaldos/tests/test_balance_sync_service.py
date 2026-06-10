from pathlib import Path

from app.core.config import Settings
from app.core.login_attempt_state import LoginAttemptState
from app.integrations.balance_portal import SantanderClientError, SantanderFailureReason
from app.integrations.galicia_selenium_client import GaliciaSeleniumClient
from app.integrations.mercadopago_api_client import MercadoPagoApiClientError
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


class FakeMercadoPagoSource(FakeSantanderSource):
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
        self.appended_balances: dict[str, MonetaryBalance] | None = None
        self._written_count = written_count

    def append_dollar_quote(
        self,
        quote: dict[str, object],
        santander_balance: MonetaryBalance | None = None,
        balances: dict[str, MonetaryBalance] | None = None,
    ) -> int:
        self.appended_quote = quote
        self.appended_balance = santander_balance
        self.appended_balances = balances
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
    assert summary.galicia_status == BalanceStatus.SKIPPED
    assert summary.mercadopago_status == BalanceStatus.SKIPPED
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
    assert sink.appended_balances is not None
    assert sink.appended_balances["santander"] == balance
    assert sink.appended_balances["galicia"].status == BalanceStatus.SKIPPED
    assert sink.appended_balances["mercadopago"].status == BalanceStatus.SKIPPED


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


def test_run_records_galicia_failure_in_separate_attempt_state(tmp_path: Path) -> None:
    settings = _settings_for_real_write(tmp_path, GALICIA_ENABLED=True)
    santander_state = _attempt_state(tmp_path, "santander")
    galicia_state = _attempt_state(tmp_path, "galicia")
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        santander_client=FakeSantanderSource(
            balance=MonetaryBalance(status=BalanceStatus.SUCCESS, source="santander")
        ),
        galicia_client=FakeSantanderSource(
            error=SantanderClientError(
                SantanderFailureReason.INCORRECT_PASSWORD,
                "bad credentials",
            )
        ),
        sheets_client=FakeDollarQuoteSink(),
        santander_attempt_state=santander_state,
        galicia_attempt_state=galicia_state,
    )

    summary = service.run()

    assert summary.santander_status == BalanceStatus.SKIPPED
    assert summary.galicia_status == BalanceStatus.FAILED
    assert summary.galicia_failure_reason == "incorrect_password"
    assert santander_state.snapshot().failed_attempts == 0
    assert galicia_state.snapshot().failed_attempts == 1


def test_run_writes_mercadopago_balance_when_enabled(tmp_path: Path) -> None:
    settings = _settings_for_real_write(
        tmp_path,
        MERCADOPAGO_ENABLED=True,
        MERCADOPAGO_ACCESS_TOKEN="token",
    )
    balance = MonetaryBalance(
        amount="4567.89",
        status=BalanceStatus.SUCCESS,
        source="mercadopago",
    )
    sink = FakeDollarQuoteSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        mercadopago_client=FakeMercadoPagoSource(balance=balance),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.mercadopago_status == BalanceStatus.SUCCESS
    assert summary.mercadopago_failure_reason is None
    assert sink.appended_balances is not None
    assert sink.appended_balances["mercadopago"] == balance


def test_run_records_mercadopago_failure_and_continues_with_sheets(tmp_path: Path) -> None:
    settings = _settings_for_real_write(
        tmp_path,
        MERCADOPAGO_ENABLED=True,
        MERCADOPAGO_ACCESS_TOKEN="token",
    )
    sink = FakeDollarQuoteSink()
    service = BalanceSyncService(
        settings=settings,
        api_client=FakeDollarQuoteSource(_dollar_quote()),
        mercadopago_client=FakeMercadoPagoSource(
            error=MercadoPagoApiClientError("report_not_ready", "not ready")
        ),
        sheets_client=sink,
    )

    summary = service.run()

    assert summary.written_count == 1
    assert summary.mercadopago_status == BalanceStatus.FAILED
    assert summary.mercadopago_failure_reason == "report_not_ready"
    assert sink.appended_balances is not None
    assert sink.appended_balances["mercadopago"].failure_reason == "report_not_ready"


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


def test_build_galicia_client_uses_selenium(tmp_path: Path) -> None:
    settings = _settings_for_real_write(
        tmp_path,
        GALICIA_ENABLED=True,
    )

    from app.services.balance_sync_service import _build_galicia_client

    assert isinstance(_build_galicia_client(settings), GaliciaSeleniumClient)


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
        "GALICIA_LOGIN_URL": "https://example.com/login",
        "GALICIA_POST_LOGIN_URL": "https://example.com/home",
        "GALICIA_DOCUMENT_NUMBER": "12345678",
        "GALICIA_DOCUMENT_NUMBER_SELECTOR": "#document",
        "GALICIA_USERNAME": "user",
        "GALICIA_PASSWORD": "password",
        "GALICIA_USERNAME_SELECTOR": "#user",
        "GALICIA_PASSWORD_SELECTOR": "#password",
        "GALICIA_SUBMIT_SELECTOR": "#submit",
        "GALICIA_BALANCE_XPATH": "//saldo",
        "GALICIA_LOGOUT_SELECTOR": "#logout",
    }
    values.update(overrides)
    return Settings(**values)


def _attempt_state(tmp_path: Path, name: str = "attempts") -> LoginAttemptState:
    return LoginAttemptState(path=tmp_path / f"{name}.json", max_attempts=2)


def _dollar_quote() -> dict[str, object]:
    return {
        "compra": 1410,
        "venta": 1430,
        "casa": "oficial",
        "nombre": "Oficial",
        "moneda": "USD",
        "fechaActualizacion": "2026-05-31T17:59:00Z",
    }
