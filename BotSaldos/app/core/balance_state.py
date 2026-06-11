"""Estado persistido de ultimos saldos exitosos por fuente."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.schemas.transaction import MonetaryBalance


@dataclass(frozen=True)
class CachedBalanceSnapshot:
    """Saldo exitoso persistido para una fuente."""

    amount: Decimal
    currency: str
    source: str
    last_updated_at: str | None


class BalanceState:
    """Persistencia JSON para reutilizar saldos cuando una fuente falla."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def get(self, source: str) -> CachedBalanceSnapshot | None:
        """Obtiene el ultimo saldo exitoso para una fuente."""
        data = self._read_data()
        balances = data.get("balances", {})
        if not isinstance(balances, dict):
            return None
        raw_balance = balances.get(source)
        if not isinstance(raw_balance, dict):
            return None

        amount = _optional_decimal(raw_balance.get("amount"))
        currency = _optional_str(raw_balance.get("currency"))
        if amount is None or currency is None:
            return None

        return CachedBalanceSnapshot(
            amount=amount,
            currency=currency,
            source=source,
            last_updated_at=_optional_str(raw_balance.get("last_updated_at")),
        )

    def save(self, balance: MonetaryBalance) -> None:
        """Persiste un saldo exitoso con monto."""
        if balance.amount is None:
            return

        data = self._read_data()
        balances = data.get("balances", {})
        if not isinstance(balances, dict):
            balances = {}

        balances[balance.source] = {
            "amount": str(balance.amount),
            "currency": balance.currency,
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_data({"balances": balances})

    def _read_data(self) -> dict[str, object]:
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def _write_data(self, data: dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None
