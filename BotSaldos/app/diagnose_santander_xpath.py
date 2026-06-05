"""Diagnostico manual para ajustar login y XPath de saldo Santander."""

from __future__ import annotations

import re
from datetime import datetime, UTC
from pathlib import Path

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.integrations.santander_client import SantanderClient
from app.integrations.web_client import WebClient


MONEY_PATTERN = re.compile(r"(?:\$|ARS)?\s*-?\d[\d.]*,\d{2}")


def main() -> None:
    """Ingresa a Santander y muestra estado de navegacion y candidatos a saldo."""
    settings = Settings()
    configure_logging(settings)
    client = SantanderClient(settings)

    with WebClient(settings).unauthenticated_page() as page:
        page.goto(settings.santander_login_url)
        client._fill_login(page)
        client._detect_login_failure(page)

        reached_home = False
        try:
            page.wait_for_url(
                settings.santander_post_login_url,
                timeout=settings.playwright_default_timeout_ms,
            )
            reached_home = True
        except Exception:
            reached_home = False

        print(f"home_url_reached: {'yes' if reached_home else 'no'}")
        print(f"current_url: {page.url}")
        print(f"title: {page.title()}")
        print(f"screenshot: {_save_screenshot(page)}")

        if not reached_home:
            print("No se llego a home; se omite diagnostico de XPath.")
            return

        configured_selector = f"xpath={settings.santander_balance_xpath}"
        try:
            locator = page.locator(configured_selector)
            locator.wait_for(timeout=5_000)
            print("XPath configurado encontrado:")
            print(f"Texto visible: {'si' if locator.inner_text().strip() else 'no'}")
        except Exception:
            print("XPath configurado no encontrado.")

        print("Candidatos monetarios visibles:")
        visible_text = page.locator("body").inner_text(timeout=10_000)
        matches = []
        for match in MONEY_PATTERN.finditer(visible_text):
            value = match.group(0).strip()
            if value not in matches:
                matches.append(value)

        for index, _value in enumerate(matches[:20], start=1):
            print(f"{index}. <monto oculto>")

        if not matches:
            print("No se encontraron textos con formato monetario en el body visible.")


def _save_screenshot(page: object) -> Path:
    screenshot_dir = Path("tmp")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    screenshot_path = screenshot_dir / f"santander_diagnose_{timestamp}.png"
    page.screenshot(path=screenshot_path, full_page=True)
    return screenshot_path


if __name__ == "__main__":
    main()
