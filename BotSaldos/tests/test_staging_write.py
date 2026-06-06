from pathlib import Path

from app.check_setup import SetupCheck
from app.core.config import Settings
from app.schemas.transaction import BalanceStatus
from app.services.balance_sync_service import SyncSummary
from app.staging_write import run_staging_write


class FakeBalanceSyncService:
    def __init__(self, summary: SyncSummary) -> None:
        self._summary = summary

    def run(self) -> SyncSummary:
        return self._summary


def test_staging_write_refuses_when_setup_fails() -> None:
    settings = Settings(_env_file=None)

    result = run_staging_write(settings=settings)

    assert result.ok is False
    assert "fallaron chequeos" in result.message


def test_staging_write_refuses_when_dry_run_is_enabled(tmp_path: Path) -> None:
    credentials = tmp_path / "service-account.json"
    credentials.write_text("{}", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        DRY_RUN=True,
        GOOGLE_APPLICATION_CREDENTIALS=credentials,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )

    result = run_staging_write(
        settings=settings,
        setup_checks=_successful_setup_checks(),
        service_factory=lambda _: FakeBalanceSyncService(
            _summary(written_count=1, dry_run=True)
        ),
    )

    assert result.ok is False
    assert "DRY_RUN=true" in result.message


def test_staging_write_reports_unexpected_written_count(tmp_path: Path) -> None:
    credentials = tmp_path / "service-account.json"
    credentials.write_text("{}", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        DRY_RUN=False,
        GOOGLE_APPLICATION_CREDENTIALS=credentials,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )

    result = run_staging_write(
        settings=settings,
        setup_checks=_successful_setup_checks(),
        service_factory=lambda _: FakeBalanceSyncService(
            _summary(written_count=0, dry_run=False)
        ),
    )

    assert result.ok is False
    assert "se escribieron 0" in result.message


def test_staging_write_passes_when_one_row_is_written(tmp_path: Path) -> None:
    credentials = tmp_path / "service-account.json"
    credentials.write_text("{}", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        DRY_RUN=False,
        GOOGLE_APPLICATION_CREDENTIALS=credentials,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )

    result = run_staging_write(
        settings=settings,
        setup_checks=_successful_setup_checks(),
        service_factory=lambda _: FakeBalanceSyncService(
            _summary(written_count=1, dry_run=False)
        ),
    )

    assert result.ok is True
    assert result.summary is not None
    assert result.summary.written_count == 1


def _successful_setup_checks() -> list[SetupCheck]:
    return [
        SetupCheck(name="google_credentials", ok=True, message="ok"),
        SetupCheck(name="google_spreadsheet_id", ok=True, message="ok"),
        SetupCheck(name="external_api", ok=True, message="ok"),
        SetupCheck(name="google_sheets_access", ok=True, message="ok"),
    ]


def _summary(written_count: int, dry_run: bool) -> SyncSummary:
    return SyncSummary(
        fetched_count=1,
        written_count=written_count,
        dry_run=dry_run,
        santander_status=BalanceStatus.SKIPPED,
        santander_failure_reason=None,
        galicia_status=BalanceStatus.SKIPPED,
        galicia_failure_reason=None,
    )
