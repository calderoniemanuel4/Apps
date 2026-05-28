from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_defaults_are_safe_for_local_scaffold() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_env == "local"
    assert settings.dry_run is True
    assert settings.log_file == Path("logs/botsaldos.log")
    assert settings.lock_file == Path("tmp/botsaldos.lock")
    assert settings.playwright_headless is True
    assert settings.google_sheets_spreadsheet_id is None


def test_real_write_requires_google_sheets_configuration() -> None:
    with pytest.raises(ValidationError, match="Falta configuracion requerida"):
        Settings(_env_file=None, DRY_RUN=False)


def test_invalid_log_level_fails_fast() -> None:
    with pytest.raises(ValidationError, match="LOG_LEVEL"):
        Settings(_env_file=None, LOG_LEVEL="VERBOSE")
