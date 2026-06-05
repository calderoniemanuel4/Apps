"""Orquestacion de sincronizacion de cotizacion del dolar."""

import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.core.login_attempt_state import LoginAttemptState
from app.integrations.api_client import ExternalApiClient
from app.integrations.santander_client import SantanderClient, SantanderClientError
from app.integrations.santander_selenium_client import SantanderSeleniumClient
from app.integrations.sheets_client import SheetsClient
from app.schemas.transaction import BalanceStatus, MonetaryBalance

logger = logging.getLogger(__name__)


class DollarQuoteSource(Protocol):
    """Contrato minimo para clientes que entregan cotizacion cruda."""

    def fetch_dollar_quote(self) -> dict[str, object]:
        """Obtiene la cotizacion cruda desde una fuente externa."""


class DollarQuoteSink(Protocol):
    """Contrato minimo para clientes que persisten cotizaciones."""

    def append_dollar_quote(
        self,
        quote: dict[str, object],
        santander_balance: MonetaryBalance | None = None,
    ) -> int:
        """Persiste la cotizacion y devuelve cuantas filas se escribieron."""


class SantanderBalanceSource(Protocol):
    """Contrato minimo para clientes que entregan saldo Santander."""

    def fetch_balance(self) -> MonetaryBalance:
        """Obtiene saldo monetario desde Santander."""


@dataclass(frozen=True)
class SyncSummary:
    """Resumen observable de una ejecucion de sincronizacion."""

    fetched_count: int
    written_count: int
    dry_run: bool
    santander_status: BalanceStatus
    santander_failure_reason: str | None


class BalanceSyncService:
    """Coordina obtencion y escritura de cotizacion del dolar."""

    def __init__(
        self,
        settings: Settings,
        api_client: DollarQuoteSource | None = None,
        santander_client: SantanderBalanceSource | None = None,
        sheets_client: DollarQuoteSink | None = None,
        santander_attempt_state: LoginAttemptState | None = None,
    ) -> None:
        self._settings = settings
        self._api_client = api_client or ExternalApiClient(settings)
        self._santander_client = santander_client or _build_santander_client(settings)
        self._sheets_client = sheets_client or SheetsClient(settings)
        self._santander_attempt_state = santander_attempt_state or LoginAttemptState(
            path=settings.santander_attempt_state_file,
            max_attempts=settings.santander_max_login_attempts,
        )

    def run(self) -> SyncSummary:
        """Ejecuta la sincronizacion completa."""
        logger.info("balance_sync_started", extra={"dry_run": self._settings.dry_run})

        santander_balance = self._fetch_santander_balance()
        dollar_quote = self._api_client.fetch_dollar_quote()
        written_count = 0

        if self._settings.dry_run:
            logger.info("dry_run_enabled_skip_sheets_write")
        else:
            written_count = self._sheets_client.append_dollar_quote(
                quote=dollar_quote,
                santander_balance=santander_balance,
            )

        summary = SyncSummary(
            fetched_count=1,
            written_count=written_count,
            dry_run=self._settings.dry_run,
            santander_status=santander_balance.status,
            santander_failure_reason=santander_balance.failure_reason,
        )

        logger.info(
            "balance_sync_finished",
            extra={
                "fetched_count": summary.fetched_count,
                "written_count": summary.written_count,
                "santander_status": summary.santander_status.value,
                "santander_failure_reason": summary.santander_failure_reason,
            },
        )
        return summary

    def _fetch_santander_balance(self) -> MonetaryBalance:
        """Consulta Santander cuando corresponde y registra intentos fallidos."""
        if not self._settings.santander_enabled:
            logger.info("santander_skipped_disabled")
            return MonetaryBalance(status=BalanceStatus.SKIPPED, source="santander")

        snapshot = self._santander_attempt_state.snapshot()
        if snapshot.blocked:
            logger.warning(
                "santander_skipped_max_attempts_reached attempts=%s last_reason=%s",
                snapshot.failed_attempts,
                snapshot.last_failure_reason,
                extra={
                    "failed_attempts": snapshot.failed_attempts,
                    "last_failure_reason": snapshot.last_failure_reason,
                },
            )
            return MonetaryBalance(
                status=BalanceStatus.BLOCKED,
                source="santander",
                failure_reason=snapshot.last_failure_reason or "max_attempts_reached",
            )

        try:
            balance = self._santander_client.fetch_balance()
        except SantanderClientError as exc:
            should_count_attempt = _should_count_as_login_attempt(exc)
            updated_snapshot = (
                self._santander_attempt_state.record_failure(exc.reason.value)
                if should_count_attempt
                else self._santander_attempt_state.snapshot()
            )
            failure_message = _sanitize_log_message(str(exc))
            logger.warning(
                "santander_balance_failed reason=%s attempts=%s blocked=%s counted=%s message=%s",
                exc.reason.value,
                updated_snapshot.failed_attempts,
                updated_snapshot.blocked,
                should_count_attempt,
                failure_message,
                extra={
                    "failure_reason": exc.reason.value,
                    "failure_message": failure_message,
                    "failed_attempts": updated_snapshot.failed_attempts,
                    "blocked": updated_snapshot.blocked,
                    "counted_as_login_attempt": should_count_attempt,
                },
            )
            return MonetaryBalance(
                status=BalanceStatus.FAILED,
                source="santander",
                failure_reason=exc.reason.value,
            )

        self._santander_attempt_state.reset()
        return balance


def _sanitize_log_message(message: str) -> str:
    sanitized = message.replace("\n", " ")
    if len(sanitized) > 240:
        return f"{sanitized[:240]}..."
    return sanitized


def _build_santander_client(settings: Settings) -> SantanderBalanceSource:
    if settings.santander_web_driver == "selenium":
        return SantanderSeleniumClient(settings)
    return SantanderClient(settings)


def _should_count_as_login_attempt(exc: SantanderClientError) -> bool:
    """Cuenta solo fallos relacionados con ingreso o disponibilidad del login."""
    non_login_failures = {"balance_not_found", "logout_failed"}
    return exc.reason.value not in non_login_failures
