"""Orquestacion de sincronizacion de saldos."""

import logging

from app.core.config import Settings
from app.integrations.api_client import ExternalApiClient
from app.integrations.sheets_client import SheetsClient
from app.integrations.web_client import WebClient
from app.schemas.transaction import Transaction

logger = logging.getLogger(__name__)


class BalanceSyncService:
    """Coordina obtencion, normalizacion y escritura de movimientos."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._api_client = ExternalApiClient(settings)
        self._web_client = WebClient(settings)
        self._sheets_client = SheetsClient(settings)

    def run(self) -> None:
        """Ejecuta la sincronizacion completa."""
        logger.info("balance_sync_started")

        raw_transactions = [
            *self._api_client.fetch_transactions(),
            *self._web_client.fetch_transactions(),
        ]
        transactions = self._normalize_transactions(raw_transactions)
        self._sheets_client.append_transactions(transactions)

        logger.info(
            "balance_sync_finished",
            extra={"raw_count": len(raw_transactions), "validated_count": len(transactions)},
        )

    def _normalize_transactions(self, raw_transactions: list[dict[str, object]]) -> list[Transaction]:
        """Convierte datos crudos en movimientos validados."""
        _ = raw_transactions
        return []
