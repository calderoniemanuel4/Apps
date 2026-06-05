"""Actualizacion controlada de headers de Google Sheets."""

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.integrations.sheets_client import SheetsClient


def main() -> None:
    """Actualiza la primera fila de la worksheet configurada."""
    settings = Settings()
    configure_logging(settings)
    headers = SheetsClient(settings).update_configured_headers()
    print("Headers actualizados:")
    print(", ".join(headers))


if __name__ == "__main__":
    main()
