from contextlib import AbstractContextManager
from decimal import Decimal
from types import TracebackType

import pytest

from app.core.config import Settings
from app.integrations.balance_portal import SantanderClientError, SantanderFailureReason
from app.integrations.santander_selenium_client import SantanderSeleniumClient, _is_logged_out


def test_fetch_balance_logs_out_before_closing_driver() -> None:
    driver = FakeDriver()
    client = FakeSantanderSeleniumClient(
        _settings(),
        selenium_client=FakeSeleniumClient(driver),
        balance_text="$ 1.234,56",
    )

    balance = client.fetch_balance()

    assert balance.amount == Decimal("1234.56")
    assert driver.logout_called is True
    assert driver.closed is True


def test_fetch_balance_logs_out_when_balance_xpath_fails() -> None:
    driver = FakeDriver()
    client = FakeSantanderSeleniumClient(
        _settings(),
        selenium_client=FakeSeleniumClient(driver),
        error=SantanderClientError(
            SantanderFailureReason.BALANCE_NOT_FOUND,
            "missing balance",
        ),
    )

    with pytest.raises(SantanderClientError) as exc_info:
        client.fetch_balance()

    assert exc_info.value.reason == SantanderFailureReason.BALANCE_NOT_FOUND
    assert driver.logout_called is True
    assert driver.closed is True


def test_is_logged_out_accepts_login_url() -> None:
    assert _is_logged_out(FakeDriver(current_url="https://example.com/#!/login")) is True


def test_is_logged_out_accepts_login_body_text() -> None:
    driver = FakeDriver(current_url="https://example.com/#!/home", body_text="Inicio de Sesión")

    assert _is_logged_out(driver) is True


def test_is_logged_out_accepts_configured_logout_url() -> None:
    driver = FakeDriver(current_url="https://www.santander.com.ar/personas/logout-plan-sueldo")

    assert _is_logged_out(
        driver,
        "https://www.santander.com.ar/personas/logout-plan-sueldo",
    ) is True


class FakeSantanderSeleniumClient(SantanderSeleniumClient):
    def __init__(
        self,
        settings: Settings,
        selenium_client: object,
        balance_text: str | None = None,
        error: SantanderClientError | None = None,
    ) -> None:
        super().__init__(settings, selenium_client=selenium_client)
        self._balance_text = balance_text
        self._error = error

    def _fill_login(self, driver: object, wait: object) -> None:
        return None

    def _wait_for_home(self, driver: object, wait: object) -> None:
        return None

    def _extract_balance_text(self, wait: object) -> str:
        if self._error is not None:
            raise self._error
        assert self._balance_text is not None
        return self._balance_text

    def _logout_safely(self, driver: object, wait: object) -> None:
        assert isinstance(driver, FakeDriver)
        assert driver.closed is False
        driver.logout_called = True


class FakeSeleniumClient:
    def __init__(self, driver: "FakeDriver") -> None:
        self._driver = driver

    def page(self) -> AbstractContextManager["FakeDriver"]:
        return FakePageContext(self._driver)


class FakePageContext:
    def __init__(self, driver: "FakeDriver") -> None:
        self._driver = driver

    def __enter__(self) -> "FakeDriver":
        return self._driver

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._driver.closed = True


class FakeDriver:
    def __init__(self, current_url: str = "", body_text: str = "") -> None:
        self.closed = False
        self.logout_called = False
        self.current_url = current_url
        self._body_text = body_text

    def get(self, url: str) -> None:
        self.url = url

    def find_element(self, by: object, value: str) -> "FakeElement":
        return FakeElement(text=self._body_text)


class FakeElement:
    def __init__(self, text: str = "") -> None:
        self.text = text


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        SANTANDER_USERNAME="user",
        SANTANDER_PASSWORD="password",
        SANTANDER_USERNAME_SELECTOR="//input[@id='user']",
        SANTANDER_PASSWORD_SELECTOR="//input[@id='password']",
        SANTANDER_SUBMIT_SELECTOR="//button[@type='submit']",
        SANTANDER_BALANCE_XPATH="//span[@id='balance']",
        SANTANDER_LOGOUT_SELECTOR="//a[@id='logout']",
        SANTANDER_LOGOUT_CONFIRM_SELECTOR="//button[@id='confirm']",
    )
