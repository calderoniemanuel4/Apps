"""Orquestacion de sincronizacion de cotizacion del dolar."""

import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.balance_state import BalanceState
from app.core.config import Settings
from app.core.login_attempt_state import LoginAttemptState
from app.core.report_state import ReportState
from app.integrations.api_client import ExternalApiClient
from app.integrations.balance_portal import BalancePortalError
from app.integrations.galicia_selenium_client import GaliciaSeleniumClient
from app.integrations.mercadopago_api_client import (
    MercadoPagoApiClient,
    MercadoPagoApiClientError,
)
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
        balances: dict[str, MonetaryBalance] | None = None,
    ) -> int:
        """Persiste la cotizacion y devuelve cuantas filas se escribieron."""


class PortalBalanceSource(Protocol):
    """Contrato minimo para clientes que entregan saldos web."""

    def fetch_balance(self) -> MonetaryBalance:
        """Obtiene saldo monetario desde un portal."""


@dataclass(frozen=True)
class SyncSummary:
    """Resumen observable de una ejecucion de sincronizacion."""

    fetched_count: int
    written_count: int
    dry_run: bool
    santander_status: BalanceStatus
    santander_failure_reason: str | None
    galicia_status: BalanceStatus
    galicia_failure_reason: str | None
    mercadopago_status: BalanceStatus
    mercadopago_failure_reason: str | None


class BalanceSyncService:
    """Coordina obtencion y escritura de cotizacion del dolar."""

    def __init__(
        self,
        settings: Settings,
        api_client: DollarQuoteSource | None = None,
        santander_client: PortalBalanceSource | None = None,
        galicia_client: PortalBalanceSource | None = None,
        mercadopago_client: PortalBalanceSource | None = None,
        sheets_client: DollarQuoteSink | None = None,
        santander_attempt_state: LoginAttemptState | None = None,
        galicia_attempt_state: LoginAttemptState | None = None,
        mercadopago_report_state: ReportState | None = None,
        balance_state: BalanceState | None = None,
    ) -> None:
        self._settings = settings
        self._api_client = api_client or ExternalApiClient(settings)
        self._santander_client = santander_client or _build_santander_client(settings)
        self._galicia_client = galicia_client or _build_galicia_client(settings)
        self._mercadopago_client = mercadopago_client or _build_mercadopago_client(
            settings,
            mercadopago_report_state,
        )
        self._sheets_client = sheets_client or SheetsClient(settings)
        self._santander_attempt_state = santander_attempt_state or LoginAttemptState(
            path=settings.santander_attempt_state_file,
            max_attempts=settings.santander_max_login_attempts,
        )
        self._galicia_attempt_state = galicia_attempt_state or LoginAttemptState(
            path=settings.galicia_attempt_state_file,
            max_attempts=settings.galicia_max_login_attempts,
        )
        self._balance_state = balance_state or BalanceState(settings.balance_state_file)

    def run(self) -> SyncSummary:
        """Ejecuta la sincronizacion completa."""
        logger.info("balance_sync_started", extra={"dry_run": self._settings.dry_run})

        santander_balance = self._with_balance_cache("santander", self._fetch_santander_balance())
        galicia_balance = self._with_balance_cache("galicia", self._fetch_galicia_balance())
        mercadopago_balance = self._with_balance_cache(
            "mercadopago",
            self._fetch_mercadopago_balance(),
        )
        dollar_quote = self._api_client.fetch_dollar_quote()
        balances = {
            "santander": santander_balance,
            "galicia": galicia_balance,
            "mercadopago": mercadopago_balance,
        }
        written_count = 0

        if self._settings.dry_run:
            logger.info("dry_run_enabled_skip_sheets_write")
        else:
            written_count = self._sheets_client.append_dollar_quote(
                quote=dollar_quote,
                santander_balance=santander_balance,
                balances=balances,
            )

        summary = SyncSummary(
            fetched_count=1,
            written_count=written_count,
            dry_run=self._settings.dry_run,
            santander_status=santander_balance.status,
            santander_failure_reason=santander_balance.failure_reason,
            galicia_status=galicia_balance.status,
            galicia_failure_reason=galicia_balance.failure_reason,
            mercadopago_status=mercadopago_balance.status,
            mercadopago_failure_reason=mercadopago_balance.failure_reason,
        )

        logger.info(
            "balance_sync_finished",
            extra={
                "fetched_count": summary.fetched_count,
                "written_count": summary.written_count,
                "santander_status": summary.santander_status.value,
                "santander_failure_reason": summary.santander_failure_reason,
                "galicia_status": summary.galicia_status.value,
                "galicia_failure_reason": summary.galicia_failure_reason,
                "mercadopago_status": summary.mercadopago_status.value,
                "mercadopago_failure_reason": summary.mercadopago_failure_reason,
            },
        )
        return summary

    def _with_balance_cache(self, source: str, balance: MonetaryBalance) -> MonetaryBalance:
        """Persiste saldos exitosos y reutiliza el ultimo ante fallas."""
        if balance.status == BalanceStatus.SUCCESS:
            self._balance_state.save(balance)
            return balance

        if balance.status not in {BalanceStatus.FAILED, BalanceStatus.BLOCKED}:
            return balance

        cached_balance = self._balance_state.get(source)
        if cached_balance is None:
            return balance

        failure_reason = _cached_failure_reason(balance)
        logger.warning(
            "%s_balance_cached_after_failure status=%s reason=%s",
            source,
            balance.status.value,
            balance.failure_reason,
            extra={
                "source": source,
                "original_status": balance.status.value,
                "failure_reason": balance.failure_reason,
                "cached_last_updated_at": cached_balance.last_updated_at,
            },
        )
        return MonetaryBalance(
            amount=cached_balance.amount,
            currency=cached_balance.currency,
            source=source,
            status=BalanceStatus.CACHED,
            failure_reason=failure_reason,
        )

    def _fetch_santander_balance(self) -> MonetaryBalance:
        """Consulta Santander cuando corresponde y registra intentos fallidos."""
        return _fetch_portal_balance(
            source="santander",
            enabled=self._settings.santander_enabled,
            client=self._santander_client,
            attempt_state=self._santander_attempt_state,
        )

    def _fetch_galicia_balance(self) -> MonetaryBalance:
        """Consulta Galicia cuando corresponde y registra intentos fallidos."""
        return _fetch_portal_balance(
            source="galicia",
            enabled=self._settings.galicia_enabled,
            client=self._galicia_client,
            attempt_state=self._galicia_attempt_state,
        )

    def _fetch_mercadopago_balance(self) -> MonetaryBalance:
        """Consulta Mercado Pago por API cuando corresponde."""
        if not self._settings.mercadopago_enabled:
            logger.info("mercadopago_skipped_disabled")
            return MonetaryBalance(status=BalanceStatus.SKIPPED, source="mercadopago")

        try:
            return self._mercadopago_client.fetch_balance()
        except MercadoPagoApiClientError as exc:
            failure_message = _sanitize_log_message(str(exc))
            logger.warning(
                "mercadopago_balance_failed reason=%s message=%s",
                exc.reason,
                failure_message,
                extra={
                    "source": "mercadopago",
                    "failure_reason": exc.reason,
                    "failure_message": failure_message,
                },
            )
            return MonetaryBalance(
                status=BalanceStatus.FAILED,
                source="mercadopago",
                failure_reason=exc.reason,
            )


def _fetch_portal_balance(
    source: str,
    enabled: bool,
    client: PortalBalanceSource,
    attempt_state: LoginAttemptState,
) -> MonetaryBalance:
    """Consulta un portal web cuando corresponde y registra intentos fallidos."""
    if not enabled:
        logger.info("%s_skipped_disabled", source)
        return MonetaryBalance(status=BalanceStatus.SKIPPED, source=source)

    snapshot = attempt_state.snapshot()
    if snapshot.blocked:
        logger.warning(
            "%s_skipped_max_attempts_reached attempts=%s last_reason=%s",
            source,
            snapshot.failed_attempts,
            snapshot.last_failure_reason,
            extra={
                "source": source,
                "failed_attempts": snapshot.failed_attempts,
                "last_failure_reason": snapshot.last_failure_reason,
            },
        )
        return MonetaryBalance(
            status=BalanceStatus.BLOCKED,
            source=source,
            failure_reason=snapshot.last_failure_reason or "max_attempts_reached",
        )

    try:
        balance = client.fetch_balance()
    except BalancePortalError as exc:
        should_count_attempt = _should_count_as_login_attempt(exc)
        updated_snapshot = (
            attempt_state.record_failure(exc.reason.value)
            if should_count_attempt
            else attempt_state.snapshot()
        )
        failure_message = _sanitize_log_message(str(exc))
        logger.warning(
            "%s_balance_failed reason=%s attempts=%s blocked=%s counted=%s message=%s",
            source,
            exc.reason.value,
            updated_snapshot.failed_attempts,
            updated_snapshot.blocked,
            should_count_attempt,
            failure_message,
            extra={
                "source": source,
                "failure_reason": exc.reason.value,
                "failure_message": failure_message,
                "failed_attempts": updated_snapshot.failed_attempts,
                "blocked": updated_snapshot.blocked,
                "counted_as_login_attempt": should_count_attempt,
            },
        )
        return MonetaryBalance(
            status=BalanceStatus.FAILED,
            source=source,
            failure_reason=exc.reason.value,
        )

    attempt_state.reset()
    return balance


def _sanitize_log_message(message: str) -> str:
    sanitized = message.replace("\n", " ")
    if len(sanitized) > 240:
        return f"{sanitized[:240]}..."
    return sanitized


def _cached_failure_reason(balance: MonetaryBalance) -> str:
    reason = balance.failure_reason or balance.status.value
    cached_reason = f"cached_after_{balance.status.value}:{reason}"
    if len(cached_reason) > 200:
        return cached_reason[:200]
    return cached_reason


def _build_santander_client(settings: Settings) -> PortalBalanceSource:
    return SantanderSeleniumClient(settings)


def _build_galicia_client(settings: Settings) -> PortalBalanceSource:
    return GaliciaSeleniumClient(settings)


def _build_mercadopago_client(
    settings: Settings,
    report_state: ReportState | None = None,
) -> PortalBalanceSource:
    return MercadoPagoApiClient(settings, report_state=report_state)


def _should_count_as_login_attempt(exc: BalancePortalError) -> bool:
    """Cuenta solo fallos relacionados con ingreso o disponibilidad del login."""
    non_login_failures = {"balance_not_found", "logout_failed"}
    return exc.reason.value not in non_login_failures
