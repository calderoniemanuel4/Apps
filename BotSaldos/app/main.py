"""Entrypoint principal de BotSaldos."""

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.services.balance_sync_service import BalanceSyncService


def main() -> None:
    """Ejecuta una sincronizacion de saldos."""
    settings = Settings()
    configure_logging(settings)

    service = BalanceSyncService(settings=settings)
    service.run()


if __name__ == "__main__":
    main()
