from decimal import Decimal

import pytest

from app.integrations.balance_portal import (
    SantanderClientError,
    SantanderFailureReason,
    parse_money,
)


def test_parse_money_accepts_argentinian_format() -> None:
    assert parse_money("$ 1.234.567,89") == Decimal("1234567.89")


def test_parse_money_accepts_argentinian_thousands_without_cents() -> None:
    assert parse_money("$ 1.234") == Decimal("1234")


def test_parse_money_accepts_decimal_dot_format() -> None:
    assert parse_money("1234.56") == Decimal("1234.56")


def test_parse_money_rejects_empty_value() -> None:
    with pytest.raises(SantanderClientError) as exc_info:
        parse_money("sin saldo")

    assert exc_info.value.reason == SantanderFailureReason.BALANCE_NOT_FOUND
