"""Integraciones de saldos web usando Selenium."""

from __future__ import annotations

import logging
import time
from typing import Any

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from app.core.config import Settings
from app.integrations.balance_portal import (
    BalancePortalConfig,
    SantanderClientError,
    SantanderFailureReason,
    parse_money,
)
from app.integrations.selenium_client import SeleniumClient, SeleniumClientError
from app.schemas.transaction import BalanceStatus, MonetaryBalance

logger = logging.getLogger(__name__)


class SeleniumBalancePortalClient:
    """Consulta un saldo monetario en un portal web con Selenium."""

    def __init__(
        self,
        settings: Settings,
        portal_config: BalancePortalConfig,
        selenium_client: SeleniumClient | None = None,
    ) -> None:
        self._settings = settings
        self._portal_config = portal_config
        self._selenium_client = selenium_client or SeleniumClient(settings)

    def fetch_balance(self) -> MonetaryBalance:
        """Ingresa al portal, extrae saldo y cierra sesion."""
        self._validate_configuration()
        reached_home = False

        try:
            with self._selenium_client.page() as driver:
                wait = WebDriverWait(driver, self._settings.selenium_page_load_timeout_ms / 1_000)
                try:
                    driver.get(self._portal_config.login_url)
                    self._fill_login(driver, wait)
                    self._wait_for_home(driver, wait)
                    reached_home = True
                    balance_text = self._extract_balance_text(wait)
                    balance = MonetaryBalance(
                        amount=parse_money(balance_text),
                        status=BalanceStatus.SUCCESS,
                        source=self._portal_config.source,
                    )
                    logger.info("%s_balance_fetched driver=selenium", self._portal_config.source)
                    return balance
                finally:
                    if reached_home:
                        self._logout_safely(driver, wait)
        except SantanderClientError:
            raise
        except SeleniumClientError as exc:
            raise SantanderClientError(
                SantanderFailureReason.UNKNOWN,
                f"No se pudo abrir navegador Selenium: {_sanitize_error(exc)}",
            ) from exc
        except TimeoutException as exc:
            raise SantanderClientError(
                SantanderFailureReason.TIMEOUT,
                f"Santander no respondio dentro del timeout configurado: {_sanitize_error(exc)}",
            ) from exc
        except WebDriverException as exc:
            raise SantanderClientError(
                SantanderFailureReason.UNKNOWN,
                f"Fallo Selenium al consultar Santander: {_sanitize_error(exc)}",
            ) from exc

    def _validate_configuration(self) -> None:
        required_values = [
            self._portal_config.submit_selector,
            self._portal_config.balance_xpath,
            self._portal_config.logout_selector,
        ]
        for value, selector in self._login_fields():
            required_values.extend([value, selector])
        if any(not value for value in required_values):
            raise SantanderClientError(
                SantanderFailureReason.MISSING_CONFIGURATION,
                f"Falta configuracion requerida para {self._portal_config.source}.",
            )

    def _fill_login(self, driver: Any, wait: WebDriverWait) -> None:
        try:
            input_elements = [
                wait.until(ec.visibility_of_element_located((By.XPATH, selector)))
                for _value, selector in self._login_fields()
            ]
            if self._portal_config.input_mode == "human":
                self._fill_login_human_like(driver, wait, input_elements)
                return

            for value, element in zip(self._login_values(), input_elements, strict=True):
                element.clear()
                element.send_keys(value)
            self._submit_login(driver, wait, input_elements[-1])
        except Exception as exc:
            raise SantanderClientError(
                SantanderFailureReason.LOGIN_FORM_NOT_FOUND,
                f"No se pudo completar el formulario de login de {self._portal_config.source}.",
            ) from exc

    def _fill_login_human_like(
        self,
        driver: Any,
        wait: WebDriverWait,
        input_elements: list[Any],
    ) -> None:
        delay_seconds = self._portal_config.type_delay_ms / 1_000
        for value, element in zip(self._login_values(), input_elements, strict=True):
            self._click_and_type_human_like(driver, element, value, delay_seconds)
            time.sleep(max(delay_seconds * 2, 0.12))
        time.sleep(max(delay_seconds * 4, 0.25))
        self._submit_login(driver, wait, input_elements[-1])

    def _click_and_type_human_like(
        self,
        driver: Any,
        element: Any,
        value: str | None,
        delay_seconds: float,
    ) -> None:
        if value is None:
            raise ValueError("Falta valor para completar login.")

        ActionChains(driver).move_to_element(element).pause(0.5).click().perform()
        element.clear()
        for character in value:
            element.send_keys(character)
            time.sleep(delay_seconds)

    def _submit_login(self, driver: Any, wait: WebDriverWait, password_input: Any) -> None:
        if self._portal_config.submit_strategy == "enter":
            password_input.send_keys("\n")
            return

        submit_button = wait.until(
            ec.element_to_be_clickable((By.XPATH, self._portal_config.submit_selector))
        )
        ActionChains(driver).move_to_element(submit_button).pause(0.5).click().perform()

    def _login_fields(self) -> list[tuple[str | None, str | None]]:
        fields: list[tuple[str | None, str | None]] = []
        if (
            self._portal_config.document_number is not None
            or self._portal_config.document_number_selector is not None
        ):
            fields.append(
                (
                    self._portal_config.document_number,
                    self._portal_config.document_number_selector,
                )
            )
        fields.extend(
            [
                (self._portal_config.username, self._portal_config.username_selector),
                (self._portal_config.password, self._portal_config.password_selector),
            ]
        )
        return fields

    def _login_values(self) -> list[str | None]:
        return [value for value, _selector in self._login_fields()]

    def _wait_for_home(self, driver: Any, wait: WebDriverWait) -> None:
        try:
            wait.until(
                lambda current_driver: current_driver.current_url
                == self._portal_config.post_login_url
            )
        except TimeoutException as exc:
            failure_reason = self._classify_login_failure(driver)
            raise SantanderClientError(
                failure_reason,
                f"{self._portal_config.source} no redirigio a home. URL actual: {driver.current_url}",
            ) from exc

    def _classify_login_failure(self, driver: Any) -> SantanderFailureReason:
        if self._selector_is_visible(driver, self._portal_config.login_error_selector):
            return SantanderFailureReason.INCORRECT_PASSWORD
        if self._selector_is_visible(driver, self._portal_config.offline_selector):
            return SantanderFailureReason.SERVICE_OFFLINE
        return SantanderFailureReason.LOGIN_NOT_COMPLETED

    @staticmethod
    def _selector_is_visible(driver: Any, selector: str | None) -> bool:
        if not selector:
            return False
        try:
            return driver.find_element(By.XPATH, selector).is_displayed()
        except Exception:
            return False

    def _extract_balance_text(self, wait: WebDriverWait) -> str:
        try:
            balance_element = wait.until(
                ec.visibility_of_element_located((By.XPATH, self._portal_config.balance_xpath))
            )
            balance_text = str(balance_element.text).strip()
        except TimeoutException as exc:
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

    def _logout_safely(self, driver: Any, wait: WebDriverWait) -> None:
        try:
            logout_button = wait.until(
                ec.element_to_be_clickable((By.XPATH, self._portal_config.logout_selector))
            )
            ActionChains(driver).move_to_element(logout_button).pause(0.2).click().perform()
            if self._portal_config.logout_confirm_selector:
                confirm_button = wait.until(
                    ec.element_to_be_clickable(
                        (By.XPATH, self._portal_config.logout_confirm_selector)
                    )
                )
                ActionChains(driver).move_to_element(confirm_button).pause(0.2).click().perform()
            if self._wait_for_logout_confirmation(driver):
                logger.info("%s_logout_completed driver=selenium", self._portal_config.source)
            else:
                logger.warning(
                    "%s_logout_not_confirmed driver=selenium current_url=%s",
                    self._portal_config.source,
                    _sanitize_error(RuntimeError(driver.current_url)),
                )
        except TimeoutException:
            logger.warning(
                "%s_logout_failed driver=selenium reason=timeout current_url=%s",
                self._portal_config.source,
                _sanitize_error(RuntimeError(driver.current_url)),
            )
        except Exception:
            logger.warning(
                "%s_logout_failed driver=selenium",
                self._portal_config.source,
                exc_info=True,
            )

    def _wait_for_logout_confirmation(self, driver: Any) -> bool:
        logout_wait = WebDriverWait(driver, self._portal_config.logout_timeout_ms / 1_000)
        try:
            logout_wait.until(_logged_out_condition(self._portal_config.logout_success_url))
            return True
        except TimeoutException:
            return False


class SantanderSeleniumClient(SeleniumBalancePortalClient):
    """Consulta saldo monetario de Santander con Selenium y Chrome."""

    def __init__(self, settings: Settings, selenium_client: SeleniumClient | None = None) -> None:
        super().__init__(
            settings=settings,
            portal_config=_santander_portal_config(settings),
            selenium_client=selenium_client,
        )


def _santander_portal_config(settings: Settings) -> BalancePortalConfig:
    return BalancePortalConfig(
        source="santander",
        login_url=settings.santander_login_url,
        post_login_url=settings.santander_post_login_url,
        username=settings.santander_username,
        password=settings.santander_password,
        username_selector=settings.santander_username_selector,
        password_selector=settings.santander_password_selector,
        submit_selector=settings.santander_submit_selector,
        balance_xpath=settings.santander_balance_xpath,
        logout_selector=settings.santander_logout_selector,
        logout_confirm_selector=settings.santander_logout_confirm_selector,
        logout_success_url=settings.santander_logout_success_url,
        login_error_selector=settings.santander_login_error_selector,
        offline_selector=settings.santander_offline_selector,
        input_mode=settings.santander_input_mode,
        submit_strategy=settings.santander_submit_strategy,
        type_delay_ms=settings.santander_type_delay_ms,
        logout_timeout_ms=settings.santander_logout_timeout_ms,
    )


def _sanitize_error(exc: Exception) -> str:
    message = str(exc).replace("\n", " ")
    if len(message) > 300:
        return f"{message[:300]}..."
    return message


def _logged_out_condition(expected_url: str | None = None) -> Any:
    def is_logged_out(driver: Any) -> bool:
        return _is_logged_out(driver, expected_url)

    return is_logged_out


def _is_logged_out(driver: Any, expected_url: str | None = None) -> bool:
    current_url = str(driver.current_url)
    if expected_url is not None and current_url.startswith(expected_url):
        return True
    if "#!/login" in current_url or "logout" in current_url.lower():
        return True
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        return False
    return "inicio de sesión" in body_text.lower() or "inicio de sesion" in body_text.lower()
