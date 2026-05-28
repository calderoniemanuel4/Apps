"""Contrato de columnas para la planilla operativa."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.schemas.transaction import Transaction


TRANSACTIONS_WORKSHEET_HEADERS: tuple[str, ...] = (
    "occurred_on",
    "description",
    "amount",
    "currency",
    "transaction_type",
    "source",
    "external_id",
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


TRANSACTIONS_WORKSHEET_CONTRACT = WorksheetContract(
    name="Movimientos",
    required_headers=TRANSACTIONS_WORKSHEET_HEADERS,
)


def transaction_to_sheet_row(transaction: Transaction) -> list[str]:
    """Convierte un movimiento validado a una fila estable para Google Sheets."""
    return [
        transaction.occurred_on.isoformat(),
        transaction.description,
        _format_decimal(transaction.amount),
        transaction.currency,
        transaction.transaction_type.value,
        transaction.source,
        transaction.external_id or "",
    ]


def _format_decimal(value: Decimal) -> str:
    """Serializa montos sin notacion cientifica ni ceros sobrantes."""
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")
