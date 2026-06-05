"""Integracion web con Santander Personas."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from app.core.config import Settings
from app.integrations.web_client import WebClient, WebClientError
from app.schemas.transaction import BalanceStatus, MonetaryBalance

logger = logging.getLogger(__name__)


class SantanderFailureReason(StrEnum):
    """Causas normalizadas de fallo al consultar Santander."""

    INCORRECT_PASSWORD = "incorrect_password"
    SERVICE_OFFLINE = "service_offline"
    NO_INTERNET = "no_internet"
    TIMEOUT = "timeout"
    MISSING_CONFIGURATION = "missing_configuration"
    LOGIN_FORM_NOT_FOUND = "login_form_not_found"
    LOGIN_NOT_COMPLETED = "login_not_completed"
    BALANCE_NOT_FOUND = "balance_not_found"
    LOGOUT_FAILED = "logout_failed"
    UNKNOWN = "unknown"


class SantanderClientError(RuntimeError):
    """Error controlado de Santander."""

    def __init__(self, reason: SantanderFailureReason, message: str) -> None:
        super().__init__(message)
        self.reason = reason


PageContextFactory = Callable[[], AbstractContextManager[Any]]


class SantanderClient:
    """Consulta saldo monetario desde Santander usando Playwright."""

    def __init__(
        self,
        settings: Settings,
        page_context_factory: PageContextFactory | None = None,
    ) -> None:
        self._settings = settings
        self._page_context_factory = page_context_factory

    def fetch_balance(self) -> MonetaryBalance:
        """Ingresa a Santander, extrae saldo y cierra sesion."""
        self._validate_configuration()

        try:
            with self._open_page() as page:
                page.goto(self._settings.santander_login_url)
                self._fill_login(page)
                self._detect_login_failure(page)
                self._wait_for_home(page)
                balance_text = self._extract_balance_text(page)
                print(balance_text)
                balance = MonetaryBalance(
                    amount=Decimal(balance_text),
                    #amount=parse_money(balance_text),
                    status=BalanceStatus.SUCCESS,
                    source="santander",
                )
                self._logout(page)
                logger.info("santander_balance_fetched")
                return balance
        except SantanderClientError:
            raise
        except WebClientError as exc:
            raise SantanderClientError(
                SantanderFailureReason.UNKNOWN,
                f"No se pudo abrir navegador Playwright: {_sanitize_error(exc)}",
            ) from exc
        except Exception as exc:
            reason = _classify_playwright_error(exc)
            raise SantanderClientError(reason, _santander_error_message(reason, exc)) from exc

    def _open_page(self) -> AbstractContextManager[Any]:
        if self._page_context_factory is not None:
            return self._page_context_factory()
        return WebClient(self._settings).unauthenticated_page()

    def _validate_configuration(self) -> None:
        required_values = [
            self._settings.santander_username,
            self._settings.santander_password,
            self._settings.santander_username_selector,
            self._settings.santander_password_selector,
            self._settings.santander_submit_selector,
            self._settings.santander_balance_xpath,
            self._settings.santander_logout_selector,
            self._settings.santander_logout_confirm_selector,
        ]
        if any(not value for value in required_values):
            raise SantanderClientError(
                SantanderFailureReason.MISSING_CONFIGURATION,
                "Falta configuracion requerida para Santander.",
            )

    def _fill_login(self, page: Any) -> None:
        try:
            self._type_like_user(
                page,
                self._settings.santander_username_selector,
                self._settings.santander_username,
            )
            password_locator = self._type_like_user(
                page,
                self._settings.santander_password_selector,
                self._settings.santander_password,
            )
            self._submit_login(page, password_locator)
        except Exception as exc:
            raise SantanderClientError(
                SantanderFailureReason.LOGIN_FORM_NOT_FOUND,
                "No se pudo completar el formulario de login de Santander.",
            ) from exc

    def _type_like_user(self, page: Any, selector: str | None, value: str | None) -> Any:
        if selector is None or value is None:
            raise ValueError("Falta selector o valor para completar login.")

        locator = page.locator(selector)
        locator.click()
        locator.fill("")
        page.keyboard.type(value, delay=self._settings.santander_type_delay_ms)
        return locator

    def _submit_login(self, page: Any, password_locator: Any) -> None:
        if self._settings.santander_submit_strategy == "enter":
            password_locator.press("Enter")
            return

        page.locator(self._settings.santander_submit_selector).click()

    def _detect_login_failure(self, page: Any) -> None:
        if self._is_visible(page, self._settings.santander_login_error_selector):
            raise SantanderClientError(
                SantanderFailureReason.INCORRECT_PASSWORD,
                "Santander rechazo las credenciales configuradas.",
            )

        if self._is_visible(page, self._settings.santander_offline_selector):
            raise SantanderClientError(
                SantanderFailureReason.SERVICE_OFFLINE,
                "Santander informa servicio fuera de linea.",
            )

    def _wait_for_home(self, page: Any) -> None:
        try:
            page.wait_for_url(
                self._settings.santander_post_login_url,
                timeout=self._settings.playwright_default_timeout_ms,
            )
        except Exception as exc:
            raise SantanderClientError(
                SantanderFailureReason.LOGIN_NOT_COMPLETED,
                f"Santander no redirigio a home. URL actual: {page.url}",
            ) from exc

    def _extract_balance_text(self, page: Any) -> str:
        selector = f"xpath={self._settings.santander_balance_xpath}"
        try:
            locator = page.locator(selector)
            locator.wait_for()
            balance_text = str(locator.inner_text()).strip()
        except Exception as exc:
            raise SantanderClientError(
                SantanderFailureReason.BALANCE_NOT_FOUND,
                "No se encontro el saldo con el XPath configurado.",
            ) from exc
        if not balance_text:
            raise SantanderClientError(
                SantanderFailureReason.BALANCE_NOT_FOUND,
                "No se encontro texto de saldo en Santander.",
            )
        return balance_text

    def _logout(self, page: Any) -> None:
        try:
            page.locator(self._settings.santander_logout_selector).click()
            page.locator(self._settings.santander_logout_confirm_selector).click()
        except Exception as exc:
            raise SantanderClientError(
                SantanderFailureReason.LOGOUT_FAILED,
                "No se pudo cerrar sesion en Santander.",
            ) from exc

    @staticmethod
    def _is_visible(page: Any, selector: str | None) -> bool:
        if not selector:
            return False
        try:
            return bool(page.locator(selector).is_visible())
        except Exception:
            return False


def parse_money(value: str) -> Decimal:
    """Parsea montos locales como `$ 1.234,56` o `1234.56`."""
    cleaned = re.sub(r"[^\d,.-]", "", value.strip())
    if not cleaned:
        raise SantanderClientError(
            SantanderFailureReason.BALANCE_NOT_FOUND,
            "No se pudo parsear el saldo monetario.",
        )

    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise SantanderClientError(
            SantanderFailureReason.BALANCE_NOT_FOUND,
            "No se pudo parsear el saldo monetario.",
        ) from exc


def _classify_playwright_error(exc: Exception) -> SantanderFailureReason:
    message = str(exc).lower()
    if (
        "net::err_internet_disconnected" in message
        or "name_not_resolved" in message
        or "err_name_not_resolved" in message
        or "err_connection" in message
    ):
        return SantanderFailureReason.NO_INTERNET
    if "err_http2_protocol_error" in message:
        return SantanderFailureReason.SERVICE_OFFLINE
    if "timeout" in message:
        return SantanderFailureReason.TIMEOUT
    return SantanderFailureReason.UNKNOWN


def _santander_error_message(reason: SantanderFailureReason, exc: Exception) -> str:
    if reason == SantanderFailureReason.NO_INTERNET:
        return "No hay conexion o no se pudo resolver Santander."
    if reason == SantanderFailureReason.SERVICE_OFFLINE:
        return f"Santander no permitio completar la navegacion: {_sanitize_error(exc)}"
    if reason == SantanderFailureReason.TIMEOUT:
        return f"Santander no respondio dentro del timeout configurado: {_sanitize_error(exc)}"
    if reason == SantanderFailureReason.BALANCE_NOT_FOUND:
        return "No se encontro el saldo con el XPath configurado."
    return f"Fallo inesperado al consultar Santander: {_sanitize_error(exc)}"


def _sanitize_error(exc: Exception) -> str:
    message = str(exc).replace("\n", " ")
    if len(message) > 300:
        return f"{message[:300]}..."
    return message
