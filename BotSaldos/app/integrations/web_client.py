"""Automatizacion web base con Playwright."""

from __future__ import annotations

import logging
import shlex
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)


class WebClientError(RuntimeError):
    """Error controlado de automatizacion web."""


class WebClient:
    """Cliente base para portales sin API oficial."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def has_storage_state(self) -> bool:
        """Indica si existe un storage state local para sesiones autenticadas."""
        return self._settings.playwright_storage_state_path.exists()

    def validate_storage_state(self) -> None:
        """Falla si no existe una sesion Playwright guardada."""
        if not self.has_storage_state():
            raise WebClientError(
                "No existe storage state de Playwright. Ejecuta login manual antes de "
                "automatizar portales autenticados."
            )

    @contextmanager
    def authenticated_page(self) -> Iterator[Any]:
        """Abre una pagina con storage state existente y la cierra al terminar."""
        self.validate_storage_state()
        with self._page(storage_state=self._settings.playwright_storage_state_path) as page:
            yield page

    @contextmanager
    def unauthenticated_page(self) -> Iterator[Any]:
        """Abre una pagina limpia para login manual o navegacion publica."""
        with self._page(storage_state=None) as page:
            yield page

    def save_storage_state_after_manual_login(self, login_url: str) -> Path:
        """Abre un navegador visible para login manual y guarda la sesion resultante."""
        if self._settings.playwright_headless:
            raise WebClientError(
                "El login manual requiere PLAYWRIGHT_HEADLESS=false para mostrar el navegador."
            )

        storage_state_path = self._settings.playwright_storage_state_path
        storage_state_path.parent.mkdir(parents=True, exist_ok=True)

        with self.unauthenticated_page() as page:
            page.goto(login_url)
            page.pause()
            page.context.storage_state(path=storage_state_path)

        logger.info("playwright_storage_state_saved")
        return storage_state_path

    @contextmanager
    def _page(self, storage_state: Path | None) -> Iterator[Any]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise WebClientError(
                "playwright no esta instalado. Instala el extra con "
                '`pip install -e ".[automation]"`.'
            ) from exc

        with sync_playwright() as playwright:
            logger.info(
                "playwright_browser_launch browser=%s channel=%s",
                self._settings.playwright_browser,
                self._settings.playwright_channel or "default",
            )
            browser_type = getattr(playwright, self._settings.playwright_browser)
            browser = browser_type.launch(**self._launch_options())
            context = browser.new_context(**self._context_options(storage_state))
            context.set_default_timeout(self._settings.playwright_default_timeout_ms)
            page = context.new_page()
            try:
                yield page
            finally:
                context.close()
                browser.close()

    def _launch_options(self) -> dict[str, object]:
        launch_options: dict[str, object] = {
            "headless": self._settings.playwright_headless,
        }
        if self._settings.playwright_channel is not None:
            launch_options["channel"] = self._settings.playwright_channel
        if self._settings.playwright_launch_args is not None:
            launch_options["args"] = shlex.split(self._settings.playwright_launch_args)
        return launch_options

    def _context_options(self, storage_state: Path | None) -> dict[str, object]:
        context_options: dict[str, object] = {
            "locale": self._settings.playwright_locale,
            "timezone_id": self._settings.playwright_timezone_id,
            "viewport": {
                "width": self._settings.playwright_viewport_width,
                "height": self._settings.playwright_viewport_height,
            },
            "extra_http_headers": {
                "Accept-Language": self._settings.playwright_accept_language,
            },
        }
        if storage_state is not None:
            context_options["storage_state"] = str(storage_state)
        return context_options
