"""Integracion Galicia usando Selenium."""

from __future__ import annotations

from app.core.config import Settings
from app.integrations.balance_portal import BalancePortalConfig
from app.integrations.santander_selenium_client import SeleniumBalancePortalClient
from app.integrations.selenium_client import SeleniumClient


class GaliciaSeleniumClient(SeleniumBalancePortalClient):
    """Consulta saldo monetario de Galicia con Selenium y Chrome."""

    def __init__(self, settings: Settings, selenium_client: SeleniumClient | None = None) -> None:
        super().__init__(
            settings=settings,
            portal_config=_galicia_portal_config(settings),
            selenium_client=selenium_client,
        )


def _galicia_portal_config(settings: Settings) -> BalancePortalConfig:
    return BalancePortalConfig(
        source="galicia",
        login_url=settings.galicia_login_url,
        post_login_url=settings.galicia_post_login_url,
        document_number=settings.galicia_document_number,
        document_number_selector=settings.galicia_document_number_selector,
        username=settings.galicia_username,
        password=settings.galicia_password,
        username_selector=settings.galicia_username_selector,
        password_selector=settings.galicia_password_selector,
        submit_selector=settings.galicia_submit_selector,
        balance_xpath=settings.galicia_balance_xpath,
        logout_selector=settings.galicia_logout_selector,
        logout_success_url=settings.galicia_logout_success_url,
        login_error_selector=settings.galicia_login_error_selector,
        offline_selector=settings.galicia_offline_selector,
        input_mode=settings.galicia_input_mode,
        submit_strategy=settings.galicia_submit_strategy,
        type_delay_ms=settings.galicia_type_delay_ms,
        logout_timeout_ms=settings.galicia_logout_timeout_ms,
    )
