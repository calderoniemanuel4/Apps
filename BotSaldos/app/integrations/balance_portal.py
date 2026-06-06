"""Contratos compartidos para portales web de saldos."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import re


class BalancePortalFailureReason(StrEnum):
    """Causas normalizadas de falla al consultar un portal web."""

    MISSING_CONFIGURATION = "missing_configuration"
    LOGIN_FORM_NOT_FOUND = "login_form_not_found"
    INCORRECT_PASSWORD = "incorrect_password"
    SERVICE_OFFLINE = "service_offline"
    NO_INTERNET = "no_internet"
    TIMEOUT = "timeout"
    LOGIN_NOT_COMPLETED = "login_not_completed"
    BALANCE_NOT_FOUND = "balance_not_found"
    LOGOUT_FAILED = "logout_failed"
    UNKNOWN = "unknown"


class BalancePortalError(RuntimeError):
    """Error controlado de un portal web de saldos."""

    def __init__(self, reason: BalancePortalFailureReason, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class BalancePortalConfig:
    """Configuracion generica para extraer un saldo desde un portal web."""

    source: str
    login_url: str
    post_login_url: str
    username: str | None
    password: str | None
    username_selector: str | None
    password_selector: str | None
    submit_selector: str | None
    balance_xpath: str | None
    logout_selector: str | None
    logout_confirm_selector: str | None
    logout_success_url: str | None = None
    input_mode: str = "direct"
    submit_strategy: str = "click"
    type_delay_ms: int = 60
    logout_timeout_ms: int = 3_000


def parse_money(value: str) -> Decimal:
    """Parsea importes argentinos y formatos decimales simples."""
    sanitized = re.sub(r"[^\d,.-]", "", value.strip())
    if not sanitized:
        raise BalancePortalError(
            BalancePortalFailureReason.BALANCE_NOT_FOUND,
            "No se pudo parsear el saldo monetario.",
        )

    if "," in sanitized:
        normalized = sanitized.replace(".", "").replace(",", ".")
    elif _looks_like_thousands_with_dots(sanitized):
        normalized = sanitized.replace(".", "")
    else:
        normalized = sanitized

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise BalancePortalError(
            BalancePortalFailureReason.BALANCE_NOT_FOUND,
            f"Saldo monetario invalido: {value}",
        ) from exc


def _looks_like_thousands_with_dots(value: str) -> bool:
    signless = value.removeprefix("-")
    if "." not in signless:
        return False
    parts = signless.split(".")
    return (
        len(parts) > 1
        and 1 <= len(parts[0]) <= 3
        and all(part.isdigit() for part in parts)
        and all(len(part) == 3 for part in parts[1:])
    )


SantanderClientError = BalancePortalError
SantanderFailureReason = BalancePortalFailureReason
