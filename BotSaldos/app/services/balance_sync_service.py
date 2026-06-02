"""Orquestacion de sincronizacion de cotizacion del dolar."""

import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.integrations.api_client import ExternalApiClient
from app.integrations.sheets_client import SheetsClient

logger = logging.getLogger(__name__)


class DollarQuoteSource(Protocol):
    """Contrato minimo para clientes que entregan cotizacion cruda."""

    def fetch_dollar_quote(self) -> dict[str, object]:
        """Obtiene la cotizacion cruda desde una fuente externa."""


class DollarQuoteSink(Protocol):
    """Contrato minimo para clientes que persisten cotizaciones."""

    def append_dollar_quote(self, quote: dict[str, object]) -> int:
        """Persiste la cotizacion y devuelve cuantas filas se escribieron."""


@dataclass(frozen=True)
class SyncSummary:
    """Resumen observable de una ejecucion de sincronizacion."""

    fetched_count: int
    written_count: int
    dry_run: bool


class BalanceSyncService:
    """Coordina obtencion y escritura de cotizacion del dolar."""

    def __init__(
        self,
        settings: Settings,
        api_client: DollarQuoteSource | None = None,
        sheets_client: DollarQuoteSink | None = None,
    ) -> None:
        self._settings = settings
        self._api_client = api_client or ExternalApiClient(settings)
        self._sheets_client = sheets_client or SheetsClient(settings)

    def run(self) -> SyncSummary:
        """Ejecuta la sincronizacion completa."""
        logger.info("balance_sync_started", extra={"dry_run": self._settings.dry_run})

        dollar_quote = self._api_client.fetch_dollar_quote()
        written_count = 0

        if self._settings.dry_run:
            logger.info("dry_run_enabled_skip_sheets_write")
        else:
            written_count = self._sheets_client.append_dollar_quote(dollar_quote)

        summary = SyncSummary(
            fetched_count=1,
            written_count=written_count,
            dry_run=self._settings.dry_run,
        )

        logger.info(
            "balance_sync_finished",
            extra={
                "fetched_count": summary.fetched_count,
                "written_count": summary.written_count,
            },
        )
        return summary
