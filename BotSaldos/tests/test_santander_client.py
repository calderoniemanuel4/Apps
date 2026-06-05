from decimal import Decimal

import pytest

from app.core.config import Settings
from app.integrations.santander_client import (
    SantanderClient,
    SantanderClientError,
    SantanderFailureReason,
    _classify_playwright_error,
    parse_money,
)


def test_parse_money_accepts_argentinian_format() -> None:
    assert parse_money("$ 1.234.567,89") == Decimal("1234567.89")


def test_parse_money_accepts_decimal_dot_format() -> None:
    assert parse_money("1234.56") == Decimal("1234.56")


def test_parse_money_rejects_empty_value() -> None:
    with pytest.raises(SantanderClientError) as exc_info:
        parse_money("sin saldo")

    assert exc_info.value.reason == SantanderFailureReason.BALANCE_NOT_FOUND


def test_classify_http2_protocol_error_as_service_offline() -> None:
    error = RuntimeError("Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR")

    assert _classify_playwright_error(error) == SantanderFailureReason.SERVICE_OFFLINE


def test_fill_login_types_values_with_configured_delay() -> None:
    settings = Settings(
        _env_file=None,
        SANTANDER_USERNAME="user",
        SANTANDER_PASSWORD="secret",
        SANTANDER_USERNAME_SELECTOR="#user",
        SANTANDER_PASSWORD_SELECTOR="#password",
        SANTANDER_SUBMIT_SELECTOR="#submit",
        SANTANDER_BALANCE_XPATH="//saldo",
        SANTANDER_LOGOUT_SELECTOR="#logout",
        SANTANDER_LOGOUT_CONFIRM_SELECTOR="#confirm",
        SANTANDER_TYPE_DELAY_MS=75,
    )
    page = FakePage()

    SantanderClient(settings)._fill_login(page)

    assert page.locator_calls == ["#user", "#password", "#submit"]
    assert page.keyboard.typed_values == [("user", 75), ("secret", 75)]
    assert page.locators["#user"].actions == ["click", "fill:"]
    assert page.locators["#password"].actions == ["click", "fill:"]
    assert page.locators["#submit"].actions == ["click"]


def test_fill_login_can_submit_with_enter() -> None:
    settings = Settings(
        _env_file=None,
        SANTANDER_USERNAME="user",
        SANTANDER_PASSWORD="secret",
        SANTANDER_USERNAME_SELECTOR="#user",
        SANTANDER_PASSWORD_SELECTOR="#password",
        SANTANDER_SUBMIT_SELECTOR="#submit",
        SANTANDER_SUBMIT_STRATEGY="enter",
        SANTANDER_BALANCE_XPATH="//saldo",
        SANTANDER_LOGOUT_SELECTOR="#logout",
        SANTANDER_LOGOUT_CONFIRM_SELECTOR="#confirm",
    )
    page = FakePage()

    SantanderClient(settings)._fill_login(page)

    assert page.locator_calls == ["#user", "#password"]
    assert page.locators["#password"].actions == ["click", "fill:", "press:Enter"]


class FakeKeyboard:
    def __init__(self) -> None:
        self.typed_values: list[tuple[str, int]] = []

    def type(self, value: str, delay: int) -> None:
        self.typed_values.append((value, delay))


class FakeLocator:
    def __init__(self) -> None:
        self.actions: list[str] = []

    def click(self) -> None:
        self.actions.append("click")

    def fill(self, value: str) -> None:
        self.actions.append(f"fill:{value}")

    def press(self, key: str) -> None:
        self.actions.append(f"press:{key}")


class FakePage:
    def __init__(self) -> None:
        self.keyboard = FakeKeyboard()
        self.locators: dict[str, FakeLocator] = {}
        self.locator_calls: list[str] = []

    def locator(self, selector: str) -> FakeLocator:
        self.locator_calls.append(selector)
        if selector not in self.locators:
            self.locators[selector] = FakeLocator()
        return self.locators[selector]
