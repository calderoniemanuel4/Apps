"""Estado persistido para reportes descargados de APIs externas."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


@dataclass(frozen=True)
class ReportStateSnapshot:
    """Estado actual de reportes procesados."""

    last_report_id: str | None
    downloaded_report_ids: frozenset[str]
    last_downloaded_at: str | None
    last_balance_amount: Decimal | None
    last_balance_currency: str | None


class ReportState:
    """Persistencia simple en JSON para no reprocesar reportes descargados."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def snapshot(self) -> ReportStateSnapshot:
        """Lee el estado actual desde disco."""
        data = self._read_data()
        downloaded_report_ids = data.get("downloaded_report_ids", [])
        if not isinstance(downloaded_report_ids, list):
            downloaded_report_ids = []

        return ReportStateSnapshot(
            last_report_id=_optional_str(data.get("last_report_id")),
            downloaded_report_ids=frozenset(str(report_id) for report_id in downloaded_report_ids),
            last_downloaded_at=_optional_str(data.get("last_downloaded_at")),
            last_balance_amount=_optional_decimal(data.get("last_balance_amount")),
            last_balance_currency=_optional_str(data.get("last_balance_currency")),
        )

    def is_downloaded(self, report_id: str) -> bool:
        """Indica si el reporte ya fue procesado."""
        return str(report_id) in self.snapshot().downloaded_report_ids

    def mark_downloaded(
        self,
        report_id: str,
        balance_amount: Decimal | None = None,
        balance_currency: str | None = None,
    ) -> ReportStateSnapshot:
        """Registra un reporte descargado correctamente."""
        snapshot = self.snapshot()
        downloaded_report_ids = set(snapshot.downloaded_report_ids)
        downloaded_report_ids.add(str(report_id))
        data: dict[str, object] = {
            "last_report_id": str(report_id),
            "downloaded_report_ids": sorted(downloaded_report_ids),
            "last_downloaded_at": datetime.now(timezone.utc).isoformat(),
            "last_balance_amount": (
                str(balance_amount)
                if balance_amount is not None
                else _optional_str(snapshot.last_balance_amount)
            ),
            "last_balance_currency": balance_currency or snapshot.last_balance_currency,
        }
        self._write_data(data)
        return self.snapshot()

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
