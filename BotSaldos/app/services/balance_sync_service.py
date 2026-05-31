"""Orquestacion de sincronizacion de saldos."""

import logging
from dataclasses import dataclass
from typing import Protocol

from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.api_client import ExternalApiClient
from app.integrations.sheets_client import SheetsClient
from app.integrations.web_client import WebClient
from app.schemas.transaction import Transaction

logger = logging.getLogger(__name__)


class TransactionSource(Protocol):
    """Contrato minimo para clientes que entregan movimientos crudos."""

    def fetch_transactions(self) -> list[dict[str, object]]:
        """Obtiene movimientos crudos desde una fuente externa."""


class TransactionSink(Protocol):
    """Contrato minimo para clientes que persisten movimientos normalizados."""

    def append_transactions(self, transactions: list[Transaction]) -> None:
        """Persiste movimientos normalizados."""


@dataclass(frozen=True)
class SyncSummary:
    """Resumen observable de una ejecucion de sincronizacion."""

    raw_count: int
    validated_count: int
    duplicate_count: int
    invalid_count: int
    written_count: int
    dry_run: bool


class BalanceSyncService:
    """Coordina obtencion, normalizacion y escritura de movimientos."""

    def __init__(
        self,
        settings: Settings,
        api_client: TransactionSource | None = None,
        web_client: TransactionSource | None = None,
        sheets_client: TransactionSink | None = None,
    ) -> None:
        self._settings = settings
        self._api_client = api_client or ExternalApiClient(settings)
        self._web_client = web_client or WebClient(settings)
        self._sheets_client = sheets_client or SheetsClient(settings)

    def run(self) -> SyncSummary:
        """Ejecuta la sincronizacion completa."""
        logger.info("balance_sync_started", extra={"dry_run": self._settings.dry_run})

        raw_transactions = [
            *self._api_client.fetch_transactions(),
            *self._web_client.fetch_transactions(),
        ]
        normalization = self._normalize_transactions(raw_transactions)
        transactions = normalization.transactions
        written_count = 0

        if self._settings.dry_run:
            logger.info("dry_run_enabled_skip_sheets_write", extra={"count": len(transactions)})
        else:
            self._sheets_client.append_transactions(transactions)
            written_count = len(transactions)

        summary = SyncSummary(
            raw_count=len(raw_transactions),
            validated_count=len(transactions),
            duplicate_count=normalization.duplicate_count,
            invalid_count=normalization.invalid_count,
            written_count=written_count,
            dry_run=self._settings.dry_run,
        )

        logger.info(
            "balance_sync_finished",
            extra={
                "raw_count": summary.raw_count,
                "validated_count": summary.validated_count,
                "duplicate_count": summary.duplicate_count,
                "invalid_count": summary.invalid_count,
                "written_count": summary.written_count,
            },
        )
        return summary

    def _normalize_transactions(
        self,
        raw_transactions: list[dict[str, object]],
    ) -> "_NormalizationResult":
        """Convierte datos crudos en movimientos validados y deduplicados."""
        transactions: list[Transaction] = []
        seen_external_ids: set[str] = set()
        duplicate_count = 0
        invalid_count = 0

        for index, raw_transaction in enumerate(raw_transactions):
            try:
                transaction = Transaction.model_validate(raw_transaction)
            except ValidationError as exc:
                invalid_count += 1
                logger.warning(
                    "invalid_transaction_skipped",
                    extra={"index": index, "error_count": len(exc.errors())},
                )
                continue

            if transaction.external_id:
                if transaction.external_id in seen_external_ids:
                    duplicate_count += 1
                    logger.info(
                        "duplicate_transaction_skipped",
                        extra={
                            "source": transaction.source,
                            "external_id": transaction.external_id,
                        },
                    )
                    continue
                seen_external_ids.add(transaction.external_id)

            transactions.append(transaction)

        return _NormalizationResult(
            transactions=transactions,
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
        )


@dataclass(frozen=True)
class _NormalizationResult:
    """Resultado interno de normalizacion."""

    transactions: list[Transaction]
    duplicate_count: int
    invalid_count: int
