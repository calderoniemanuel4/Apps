"""Cliente HTTP para reportes de dinero liberado de Mercado Pago."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Any

import httpx

from app.core.config import Settings
from app.core.report_state import ReportState
from app.schemas.transaction import BalanceStatus, MonetaryBalance

logger = logging.getLogger(__name__)

READY_REPORT_STATUSES = frozenset({"enabled", "processed"})


class MercadoPagoApiClientError(RuntimeError):
    """Error controlado al consultar reportes de Mercado Pago."""

    def __init__(self, reason: str, message: str) -> None:
        self.reason = reason
        super().__init__(message)


@dataclass(frozen=True)
class ReleaseReportRequest:
    """Rango exacto solicitado para generar un reporte."""

    begin_date: str
    end_date: str

    def as_payload(self) -> dict[str, str]:
        """Devuelve el JSON esperado por Mercado Pago."""
        return {
            "begin_date": self.begin_date,
            "end_date": self.end_date,
        }


class MercadoPagoApiClient:
    """Obtiene el saldo monetario desde el reporte `release_report` de Mercado Pago."""

    def __init__(
        self,
        settings: Settings,
        report_state: ReportState | None = None,
        http_client: httpx.Client | None = None,
        sleeper: Any = time.sleep,
        clock: Any | None = None,
    ) -> None:
        self._settings = settings
        self._report_state = report_state or ReportState(settings.mercadopago_report_state_file)
        self._http_client = http_client
        self._sleeper = sleeper
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch_balance(self) -> MonetaryBalance:
        """Genera, descarga y parsea el ultimo reporte esperado."""
        request = self._build_report_request()
        client = self._http_client or httpx.Client(timeout=self._settings.mercadopago_timeout_seconds)
        close_client = self._http_client is None

        try:
            generation_request_id: str | None = None
            try:
                latest_report = self._fetch_latest_report(client, request)
            except MercadoPagoApiClientError as exc:
                if exc.reason not in {"report_not_ready", "latest_report_mismatch", "report_list_empty"}:
                    raise
                generation_request_id = self._request_report_generation(client, request)
                latest_report = self._wait_for_latest_report(client, request)

            report_id = self._extract_report_id(latest_report)
            currency = str(latest_report.get("currency_id") or "ARS")

            if self._report_state.is_downloaded(report_id):
                snapshot = self._report_state.snapshot()
                try:
                    generation_request_id = self._request_report_generation(client, request)
                    latest_report = self._wait_for_new_report(client, request, previous_report_id=report_id)
                    report_id = self._extract_report_id(latest_report)
                    currency = str(latest_report.get("currency_id") or "ARS")
                except MercadoPagoApiClientError as exc:
                    if exc.reason not in {"report_not_ready", "latest_report_mismatch", "report_list_empty"}:
                        raise
                    if snapshot.last_balance_amount is not None:
                        logger.info(
                            "mercadopago_report_reused_last_balance",
                            extra={"report_id": report_id, "reason": exc.reason},
                        )
                        return MonetaryBalance(
                            amount=snapshot.last_balance_amount,
                            currency=snapshot.last_balance_currency or currency,
                            status=BalanceStatus.SUCCESS,
                            source="mercadopago",
                        )

                    logger.info(
                        "mercadopago_report_redownload_for_balance_cache",
                        extra={"report_id": report_id, "reason": exc.reason},
                    )

            file_name = self._extract_file_name(latest_report)
            csv_text = self._download_report(client, file_name)
            balance_amount = self._extract_amount_balance(csv_text)
            self._report_state.mark_downloaded(
                report_id,
                balance_amount=balance_amount,
                balance_currency=currency,
            )

            logger.info(
                "mercadopago_balance_fetched",
                extra={
                    "generation_request_id": generation_request_id,
                    "report_id": report_id,
                    "file_name": file_name,
                },
            )
            return MonetaryBalance(
                amount=balance_amount,
                currency=currency,
                status=BalanceStatus.SUCCESS,
                source="mercadopago",
            )
        except MercadoPagoApiClientError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, InvalidOperation) as exc:
            raise MercadoPagoApiClientError(
                "unexpected_error",
                "No se pudo obtener el saldo desde Mercado Pago",
            ) from exc
        finally:
            if close_client:
                client.close()

    def _request_report_generation(
        self,
        client: httpx.Client,
        request: ReleaseReportRequest,
    ) -> str | None:
        response = client.post(
            self._settings.mercadopago_release_report_url,
            headers=self._headers(),
            json=request.as_payload(),
        )
        if response.status_code == 203:
            raise MercadoPagoApiClientError(
                "report_generation_rejected",
                "Mercado Pago no pudo crear el reporte para el rango solicitado",
            )
        if response.status_code not in {200, 202}:
            raise MercadoPagoApiClientError(
                "report_generation_failed",
                f"Mercado Pago respondio {response.status_code} al crear el reporte",
            )
        generation_request_id = _extract_optional_response_id(response)
        logger.info(
            "mercadopago_release_report_requested",
            extra={
                "begin_date": request.begin_date,
                "end_date": request.end_date,
                "generation_request_id": generation_request_id,
            },
        )
        return generation_request_id

    def _wait_for_latest_report(
        self,
        client: httpx.Client,
        request: ReleaseReportRequest,
    ) -> dict[str, object]:
        max_attempts = self._settings.mercadopago_report_max_attempts
        last_error: MercadoPagoApiClientError | None = None

        for attempt_number in range(1, max_attempts + 1):
            self._wait_before_report_list(attempt_number)
            try:
                return self._fetch_latest_report(client, request)
            except MercadoPagoApiClientError as exc:
                if exc.reason not in {"report_not_ready", "latest_report_mismatch", "report_list_empty"}:
                    raise
                last_error = exc
                logger.info(
                    "mercadopago_release_report_pending",
                    extra={
                        "attempt": attempt_number,
                        "max_attempts": max_attempts,
                        "reason": exc.reason,
                    },
                )

        reason = last_error.reason if last_error is not None else "report_not_ready"
        message = (
            str(last_error)
            if last_error is not None
            else "El reporte de Mercado Pago no estuvo listo dentro del limite de intentos"
        )
        raise MercadoPagoApiClientError(reason, message)

    def _wait_for_new_report(
        self,
        client: httpx.Client,
        request: ReleaseReportRequest,
        previous_report_id: str,
    ) -> dict[str, object]:
        max_attempts = self._settings.mercadopago_report_max_attempts
        last_error: MercadoPagoApiClientError | None = None

        for attempt_number in range(1, max_attempts + 1):
            self._wait_before_report_list(attempt_number)
            try:
                latest_report = self._fetch_latest_report(client, request)
            except MercadoPagoApiClientError as exc:
                if exc.reason not in {"report_not_ready", "latest_report_mismatch", "report_list_empty"}:
                    raise
                last_error = exc
                logger.info(
                    "mercadopago_release_report_pending",
                    extra={
                        "attempt": attempt_number,
                        "max_attempts": max_attempts,
                        "reason": exc.reason,
                    },
                )
                continue

            latest_report_id = self._extract_report_id(latest_report)
            if latest_report_id != previous_report_id:
                return latest_report

            last_error = MercadoPagoApiClientError(
                "report_not_ready",
                "Mercado Pago todavia devuelve el mismo reporte descargado",
            )
            logger.info(
                "mercadopago_release_report_pending",
                extra={
                    "attempt": attempt_number,
                    "max_attempts": max_attempts,
                    "reason": "same_report_id",
                    "report_id": latest_report_id,
                },
            )

        reason = last_error.reason if last_error is not None else "report_not_ready"
        message = (
            str(last_error)
            if last_error is not None
            else "El reporte nuevo de Mercado Pago no estuvo listo dentro del limite de intentos"
        )
        raise MercadoPagoApiClientError(reason, message)

    def _wait_before_report_list(self, attempt_number: int) -> None:
        delay = self._settings.mercadopago_report_wait_seconds
        if delay <= 0:
            return
        logger.info(
            "mercadopago_release_report_wait_started",
            extra={"attempt": attempt_number, "delay_seconds": delay},
        )
        self._sleeper(delay)

    def _fetch_latest_report(
        self,
        client: httpx.Client,
        request: ReleaseReportRequest,
    ) -> dict[str, object]:
        response = client.get(
            self._settings.mercadopago_release_report_list_url,
            headers=self._headers(),
        )
        if response.status_code != 200:
            raise MercadoPagoApiClientError(
                "report_list_failed",
                f"Mercado Pago respondio {response.status_code} al listar reportes",
            )

        payload = response.json()
        if not isinstance(payload, list) or not payload:
            raise MercadoPagoApiClientError("report_list_empty", "Mercado Pago no devolvio reportes")

        latest_report = payload[0]
        if not isinstance(latest_report, dict):
            raise MercadoPagoApiClientError("invalid_report_list", "El ultimo reporte no es JSON")

        status = str(latest_report.get("status") or "").lower()
        if status not in READY_REPORT_STATUSES:
            raise MercadoPagoApiClientError(
                "report_not_ready",
                f"El ultimo reporte de Mercado Pago aun no esta listo: {status or 'unknown'}",
            )

        if not self._matches_requested_range(latest_report, request):
            raise MercadoPagoApiClientError(
                "latest_report_mismatch",
                "El ultimo reporte de Mercado Pago no coincide con el rango solicitado",
            )

        return latest_report

    def _download_report(self, client: httpx.Client, file_name: str) -> str:
        response = client.get(
            f"{self._settings.mercadopago_release_report_download_url.rstrip('/')}/{file_name}",
            headers=self._headers(),
        )
        if response.status_code != 200:
            raise MercadoPagoApiClientError(
                "report_download_failed",
                f"Mercado Pago respondio {response.status_code} al descargar el reporte",
            )
        return response.text

    def _extract_amount_balance(self, csv_text: str) -> Decimal:
        try:
            import pandas as pd
        except ImportError as exc:
            raise MercadoPagoApiClientError(
                "pandas_not_installed",
                "pandas no esta instalado para leer el CSV de Mercado Pago",
            ) from exc

        dataframe = pd.read_csv(StringIO(csv_text), sep=None, engine="python")
        if dataframe.empty:
            raise MercadoPagoApiClientError("empty_report", "El CSV de Mercado Pago esta vacio")

        amount_column = _find_column(dataframe.columns, "BALANCE_AMOUNT")
        if amount_column is None:
            raise MercadoPagoApiClientError(
                "balance_amount_not_found",
                "El CSV de Mercado Pago no contiene la columna BALANCE_AMOUNT",
            )

        balance_rows = dataframe
        date_column = _find_column(dataframe.columns, "DATE")
        if date_column is not None:
            date_values = dataframe[date_column].fillna("").astype(str).str.strip()
            dated_rows = dataframe[date_values != ""]
            if not dated_rows.empty:
                balance_rows = dated_rows

        values = balance_rows[amount_column].dropna()
        if values.empty:
            raise MercadoPagoApiClientError(
                "balance_amount_empty",
                "La columna BALANCE_AMOUNT no contiene valores",
            )

        return _parse_decimal_amount(values.iloc[-1])

    def _build_report_request(self) -> ReleaseReportRequest:
        end_date = self._clock()
        begin_date = end_date - timedelta(hours=24)
        return ReleaseReportRequest(
            begin_date=_format_api_datetime(begin_date),
            end_date=_format_api_datetime(end_date),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._settings.mercadopago_access_token}",
        }

    def _extract_report_id(self, report: dict[str, object]) -> str:
        report_id = report.get("id")
        if report_id is None:
            raise MercadoPagoApiClientError("report_id_not_found", "El reporte no contiene id")
        return str(report_id)

    def _extract_file_name(self, report: dict[str, object]) -> str:
        file_name = report.get("file_name_report", report.get("file_name"))
        if not file_name:
            raise MercadoPagoApiClientError(
                "file_name_not_found",
                "El reporte no contiene file_name_report",
            )
        return str(file_name)

    def _matches_requested_range(
        self,
        report: dict[str, object],
        request: ReleaseReportRequest,
    ) -> bool:
        if not self._settings.mercadopago_validate_report_range:
            return True
        return (
            str(report.get("begin_date") or "") == request.begin_date
            and str(report.get("end_date") or "") == request.end_date
        )


def _format_api_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_column(columns: Any, expected_name: str) -> str | None:
    normalized_expected = expected_name.lower()
    for column in columns:
        if str(column).strip().lower() == normalized_expected:
            return str(column)
    return None


def _parse_decimal_amount(value: object) -> Decimal:
    raw_value = str(value).strip()
    if not raw_value:
        raise InvalidOperation

    normalized = raw_value.replace("$", "").replace(" ", "")
    has_comma = "," in normalized
    has_dot = "." in normalized

    if has_comma and has_dot:
        if normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
    elif has_comma:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif has_dot and normalized.count(".") > 1:
        normalized = normalized.replace(".", "")

    return Decimal(normalized)


def _extract_optional_response_id(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    response_id = payload.get("id")
    if response_id is None:
        return None
    return str(response_id)
