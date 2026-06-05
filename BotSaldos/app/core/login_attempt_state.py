"""Estado persistido para intentos de login en portales web."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class LoginAttemptSnapshot:
    """Estado actual de intentos fallidos."""

    failed_attempts: int
    blocked: bool
    last_failure_reason: str | None
    last_failed_at: str | None


class LoginAttemptState:
    """Persistencia simple en JSON para controlar reintentos de login."""

    def __init__(self, path: Path, max_attempts: int) -> None:
        self._path = path
        self._max_attempts = max_attempts

    def snapshot(self) -> LoginAttemptSnapshot:
        """Lee el estado actual desde disco."""
        data = self._read_data()
        failed_attempts = int(data.get("failed_attempts", 0))
        return LoginAttemptSnapshot(
            failed_attempts=failed_attempts,
            blocked=failed_attempts >= self._max_attempts,
            last_failure_reason=_optional_str(data.get("last_failure_reason")),
            last_failed_at=_optional_str(data.get("last_failed_at")),
        )

    def can_attempt(self) -> bool:
        """Indica si aun se puede intentar login automatico."""
        return not self.snapshot().blocked

    def record_failure(self, reason: str) -> LoginAttemptSnapshot:
        """Registra un fallo e incrementa el contador."""
        snapshot = self.snapshot()
        failed_attempts = snapshot.failed_attempts + 1
        self._write_data(
            {
                "failed_attempts": failed_attempts,
                "last_failure_reason": reason,
                "last_failed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return self.snapshot()

    def reset(self) -> None:
        """Limpia el contador despues de una consulta exitosa o revision manual."""
        self._write_data(
            {
                "failed_attempts": 0,
                "last_failure_reason": None,
                "last_failed_at": None,
            }
        )

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
