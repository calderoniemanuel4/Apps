from pathlib import Path

from app.core.config import Settings


def test_settings_defaults_are_safe_for_local_scaffold() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_env == "local"
    assert settings.log_file == Path("logs/botsaldos.log")
    assert settings.playwright_headless is True
    assert settings.google_sheets_spreadsheet_id is None
