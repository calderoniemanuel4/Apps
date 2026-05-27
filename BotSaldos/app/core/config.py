"""Configuracion centralizada de BotSaldos."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings cargados desde variables de entorno o archivo `.env` local."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Path = Field(default=Path("logs/botsaldos.log"), alias="LOG_FILE")

    google_application_credentials: Path | None = Field(
        default=None,
        alias="GOOGLE_APPLICATION_CREDENTIALS",
    )
    google_sheets_spreadsheet_id: str | None = Field(
        default=None,
        alias="GOOGLE_SHEETS_SPREADSHEET_ID",
    )
    google_sheets_worksheet_name: str = Field(
        default="Movimientos",
        alias="GOOGLE_SHEETS_WORKSHEET_NAME",
    )

    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")
    playwright_storage_state_path: Path = Field(
        default=Path("playwright/.auth/storage_state.json"),
        alias="PLAYWRIGHT_STORAGE_STATE_PATH",
    )

    external_api_timeout_seconds: int = Field(default=20, alias="EXTERNAL_API_TIMEOUT_SECONDS")
