"""Lock de ejecucion para evitar corridas simultaneas desde cron."""

from __future__ import annotations

import os
from pathlib import Path
from types import TracebackType


class ExecutionLockError(RuntimeError):
    """Error lanzado cuando ya existe una ejecucion activa."""


class ExecutionLock:
    """Lockfile simple basado en creacion atomica de archivo."""

    def __init__(self, lock_file: Path) -> None:
        self._lock_file = lock_file
        self._file_descriptor: int | None = None

    def __enter__(self) -> "ExecutionLock":
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._file_descriptor = os.open(
                self._lock_file,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as exc:
            raise ExecutionLockError(f"Ya existe una ejecucion activa: {self._lock_file}") from exc

        pid = str(os.getpid()).encode("utf-8")
        os.write(self._file_descriptor, pid)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._file_descriptor is not None:
            os.close(self._file_descriptor)
            self._file_descriptor = None

        self._lock_file.unlink(missing_ok=True)
