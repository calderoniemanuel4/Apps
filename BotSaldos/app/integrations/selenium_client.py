"""Automatizacion web base con Selenium."""

from __future__ import annotations

import logging
import shlex
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)


class SeleniumClientError(RuntimeError):
    """Error controlado de automatizacion Selenium."""


class SeleniumClient:
    """Cliente base Selenium para automatizar portales web."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @contextmanager
    def page(self) -> Iterator[Any]:
        """Abre Chrome con Selenium y lo cierra al terminar."""
        try:
            from selenium import webdriver
        except ImportError as exc:
            raise SeleniumClientError(
                "selenium no esta instalado. Instala el extra con "
                '`pip install -e ".[automation]"`.'
            ) from exc

        logger.info(
            "selenium_browser_launch headless=%s args=%s",
            self._settings.selenium_headless,
            self._settings.selenium_launch_args or "",
        )
        driver = webdriver.Chrome(options=self._chrome_options())
        driver.set_page_load_timeout(self._settings.selenium_page_load_timeout_ms / 1_000)
        self._configure_headers(driver)
        try:
            yield driver
        finally:
            driver.quit()

    def _chrome_options(self) -> Any:
        try:
            from selenium.webdriver.chrome.options import Options
        except ImportError as exc:
            raise SeleniumClientError("selenium no esta instalado correctamente.") from exc

        options = Options()
        options.add_argument(
            f"--window-size={self._settings.selenium_window_width},"
            f"{self._settings.selenium_window_height}"
        )
        options.add_argument(f"--lang={self._settings.selenium_accept_language.split(',')[0]}")

        if self._settings.selenium_headless:
            options.add_argument("--headless=new")
        if self._settings.selenium_user_agent is not None:
            options.add_argument(f"--user-agent={self._settings.selenium_user_agent}")
        for launch_arg in self._launch_args():
            options.add_argument(launch_arg)
        options.set_capability(
            "goog:loggingPrefs",
            {
                "browser": "ALL",
                "performance": "ALL",
            },
        )

        return options

    def _launch_args(self) -> list[str]:
        if self._settings.selenium_launch_args is None:
            return []
        return shlex.split(self._settings.selenium_launch_args)

    def _configure_headers(self, driver: Any) -> None:
        headers = {"Accept-Language": self._settings.selenium_accept_language}
        try:
            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})
        except Exception:
            logger.warning("selenium_cdp_headers_failed", exc_info=True)
