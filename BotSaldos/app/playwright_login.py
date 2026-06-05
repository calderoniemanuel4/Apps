"""Login manual asistido para guardar storage state de Playwright."""

from __future__ import annotations

import os

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.integrations.web_client import WebClient


def main() -> None:
    """Abre un navegador visible y guarda la sesion luego del login manual."""
    login_url = os.getenv("PLAYWRIGHT_LOGIN_URL")
    if not login_url:
        raise SystemExit("Falta PLAYWRIGHT_LOGIN_URL para iniciar login manual.")

    settings = Settings(PLAYWRIGHT_HEADLESS=False)
    configure_logging(settings)
    storage_state_path = WebClient(settings).save_storage_state_after_manual_login(login_url)
    print(f"Storage state guardado en: {storage_state_path}")


if __name__ == "__main__":
    main()
