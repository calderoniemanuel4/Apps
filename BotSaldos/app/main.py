"""Entrypoint principal de BotSaldos."""

from app.core.config import Settings
from app.core.execution_lock import ExecutionLock
from app.core.logging_config import configure_logging
from app.services.balance_sync_service import BalanceSyncService


def main() -> None:
    """Ejecuta una sincronizacion de saldos."""
    settings = Settings()
    configure_logging(settings)

    with ExecutionLock(settings.lock_file):
        service = BalanceSyncService(settings=settings)
        service.run()


if __name__ == "__main__":
    main()
