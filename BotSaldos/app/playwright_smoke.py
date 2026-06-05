"""Smoke test local de Playwright."""

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.integrations.web_client import WebClient


def main() -> None:
    """Verifica que Chromium puede abrir una pagina local simple."""
    settings = Settings(PLAYWRIGHT_HEADLESS=True)
    configure_logging(settings)

    with WebClient(settings).unauthenticated_page() as page:
        page.goto("data:text/html,<title>ok</title><h1>BotSaldos</h1>")
        title = page.title()

    if title != "ok":
        raise SystemExit(f"Playwright respondio con titulo inesperado: {title}")

    print("Playwright smoke OK")


if __name__ == "__main__":
    main()
