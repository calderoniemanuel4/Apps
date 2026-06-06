"""Contrato de columnas para la planilla operativa."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.schemas.transaction import MonetaryBalance


ARGENTINA_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
SHEET_DATETIME_FORMAT = "%d-%m-%Y  %H:%M:%S"

USD_QUOTE_WORKSHEET_HEADERS: tuple[str, ...] = (
    "fetched_at",
    "santander_balance",
    "santander_currency",
    "santander_status",
    "santander_failure_reason",
    "compra",
    "venta",
    "casa",
    "nombre",
    "moneda",
    "fecha_actualizacion",
    "raw_response",
)


class SheetContractError(ValueError):
    """Error de contrato entre BotSaldos y la planilla."""


@dataclass(frozen=True)
class WorksheetContract:
    """Define y valida el contrato minimo de una worksheet."""

    name: str
    required_headers: tuple[str, ...]

    def validate_headers(self, headers: list[str]) -> None:
        """Valida que la worksheet tenga exactamente los encabezados esperados."""
        normalized_headers = tuple(header.strip() for header in headers)
        if normalized_headers == self.required_headers:
            return

        raise SheetContractError(
            "Encabezados invalidos para worksheet "
            f"{self.name!r}. Esperados: {list(self.required_headers)}. "
            f"Recibidos: {list(normalized_headers)}"
        )


USD_QUOTE_WORKSHEET_CONTRACT = WorksheetContract(
    name="Cotizaciones",
    required_headers=USD_QUOTE_WORKSHEET_HEADERS,
)


def dollar_quote_to_sheet_row(
    quote: dict[str, object],
    santander_balance: MonetaryBalance | None = None,
    fetched_at: datetime | None = None,
) -> list[str]:
    """Convierte la respuesta cruda de DolarApi a una fila estable para Google Sheets."""
    observed_at = fetched_at or datetime.now(timezone.utc)
    balance = santander_balance or MonetaryBalance(status="skipped", source="santander")
    return [
        _format_sheet_datetime(observed_at),
        _stringify_optional(balance.amount),
        balance.currency,
        balance.status.value,
        _stringify_optional(balance.failure_reason),
        _stringify_optional(quote.get("compra")),
        _stringify_optional(quote.get("venta")),
        _stringify_optional(quote.get("casa")),
        _stringify_optional(quote.get("nombre")),
        _stringify_optional(quote.get("moneda")),
        _stringify_optional(quote.get("fechaActualizacion")),
        json.dumps(quote, ensure_ascii=True, sort_keys=True),
    ]


def _stringify_optional(value: object) -> str:
    """Serializa valores simples de API manteniendo celdas vacias para ausentes."""
    if value is None:
        return ""
    return str(value)


def _format_sheet_datetime(value: datetime) -> str:
    """Formatea fecha/hora para planilla en horario de Argentina."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    argentina_time = value.astimezone(ARGENTINA_TIMEZONE)
    return argentina_time.strftime(SHEET_DATETIME_FORMAT)
