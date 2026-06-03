"""Prueba controlada de escritura contra una planilla de staging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.check_setup import SetupCheck, run_setup_checks
from app.core.config import Settings
from app.core.execution_lock import ExecutionLock
from app.core.logging_config import configure_logging
from app.services.balance_sync_service import BalanceSyncService, SyncSummary


@dataclass(frozen=True)
class StagingWriteResult:
    """Resultado de una prueba de escritura controlada."""

    ok: bool
    message: str
    summary: SyncSummary | None = None


def run_staging_write(
    settings: Settings,
    service_factory: Callable[[Settings], BalanceSyncService] | None = None,
    setup_checks: list[SetupCheck] | None = None,
) -> StagingWriteResult:
    """Valida setup y escribe una cotizacion solo si `DRY_RUN=false`."""
    checks = setup_checks if setup_checks is not None else run_setup_checks(settings)
    failed_checks = [check for check in checks if not check.ok]
    if failed_checks:
        return StagingWriteResult(
            ok=False,
            message=_format_failed_checks(failed_checks),
        )

    if settings.dry_run:
        return StagingWriteResult(
            ok=False,
            message="DRY_RUN=true. Cambiar a DRY_RUN=false solo contra staging validado.",
        )

    service = (
        service_factory(settings)
        if service_factory
        else BalanceSyncService(settings=settings)
    )
    summary = service.run()
    if summary.written_count != 1:
        return StagingWriteResult(
            ok=False,
            message=f"Se esperaban 1 filas escritas y se escribieron {summary.written_count}.",
            summary=summary,
        )

    return StagingWriteResult(
        ok=True,
        message="Escritura de staging completada correctamente.",
        summary=summary,
    )


def main() -> None:
    """Entrypoint CLI para una primera escritura controlada."""
    settings = Settings()
    configure_logging(settings)

    with ExecutionLock(settings.lock_file):
        result = run_staging_write(settings)

    status = "OK" if result.ok else "FAIL"
    print(f"[{status}] staging_write: {result.message}")

    if result.summary is not None:
        print(
            "[INFO] summary: "
            f"fetched_count={result.summary.fetched_count} "
            f"written_count={result.summary.written_count} "
            f"dry_run={result.summary.dry_run}"
        )

    if not result.ok:
        raise SystemExit(1)


def _format_failed_checks(failed_checks: list[SetupCheck]) -> str:
    joined = "; ".join(f"{check.name}: {check.message}" for check in failed_checks)
    return f"No se ejecuta escritura porque fallaron chequeos de setup: {joined}"


if __name__ == "__main__":
    main()
