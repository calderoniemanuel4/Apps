from pathlib import Path

from app.check_setup import run_setup_checks
from app.core.config import Settings


class FakeApiClient:
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    def fetch_dollar_quote(self) -> dict[str, object]:
        if self._should_fail:
            raise RuntimeError("api unavailable")
        return {"venta": 1430, "nombre": "Oficial"}


class FakeSheetsClient:
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    def validate_configured_worksheet(self) -> list[str]:
        if self._should_fail:
            raise RuntimeError("worksheet unavailable")
        return ["fetched_at", "compra"]


def test_run_setup_checks_passes_with_configured_dependencies(tmp_path: Path) -> None:
    credentials = tmp_path / "service-account.json"
    credentials.write_text("{}", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        GOOGLE_APPLICATION_CREDENTIALS=credentials,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )

    checks = run_setup_checks(
        settings=settings,
        api_client=FakeApiClient(),
        sheets_client=FakeSheetsClient(),
    )

    assert all(check.ok for check in checks)


def test_run_setup_checks_reports_missing_google_configuration() -> None:
    settings = Settings(_env_file=None)

    checks = run_setup_checks(
        settings=settings,
        api_client=FakeApiClient(),
        sheets_client=FakeSheetsClient(),
    )

    failed_names = {check.name for check in checks if not check.ok}
    assert failed_names == {
        "google_credentials",
        "google_spreadsheet_id",
        "google_sheets_access",
    }


def test_run_setup_checks_reports_external_api_failure(tmp_path: Path) -> None:
    credentials = tmp_path / "service-account.json"
    credentials.write_text("{}", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        GOOGLE_APPLICATION_CREDENTIALS=credentials,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )

    checks = run_setup_checks(
        settings=settings,
        api_client=FakeApiClient(should_fail=True),
        sheets_client=FakeSheetsClient(),
    )

    external_api_check = next(check for check in checks if check.name == "external_api")
    assert external_api_check.ok is False


def test_run_setup_checks_reports_google_sheets_failure(tmp_path: Path) -> None:
    credentials = tmp_path / "service-account.json"
    credentials.write_text("{}", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        GOOGLE_APPLICATION_CREDENTIALS=credentials,
        GOOGLE_SHEETS_SPREADSHEET_ID="sheet-id",
    )

    checks = run_setup_checks(
        settings=settings,
        api_client=FakeApiClient(),
        sheets_client=FakeSheetsClient(should_fail=True),
    )

    sheets_check = next(check for check in checks if check.name == "google_sheets_access")
    assert sheets_check.ok is False
