"""Configuracion centralizada de BotSaldos."""

from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings cargados desde variables de entorno o archivo `.env` local."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    dry_run: bool = Field(default=True, alias="DRY_RUN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Path = Field(default=Path("logs/botsaldos.log"), alias="LOG_FILE")
    lock_file: Path = Field(default=Path("tmp/botsaldos.lock"), alias="LOCK_FILE")

    google_application_credentials: Path | None = Field(
        default=None,
        alias="GOOGLE_APPLICATION_CREDENTIALS",
    )
    google_sheets_spreadsheet_id: str | None = Field(
        default=None,
        alias="GOOGLE_SHEETS_SPREADSHEET_ID",
    )
    google_sheets_worksheet_name: str = Field(
        default="Cotizaciones",
        alias="GOOGLE_SHEETS_WORKSHEET_NAME",
    )

    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")
    playwright_storage_state_path: Path = Field(
        default=Path("playwright/.auth/storage_state.json"),
        alias="PLAYWRIGHT_STORAGE_STATE_PATH",
    )

    external_api_timeout_seconds: int = Field(default=20, alias="EXTERNAL_API_TIMEOUT_SECONDS")
    external_api_dollar_quote_url: str = Field(
        default="https://dolarapi.com/v1/dolares/oficial",
        alias="EXTERNAL_API_DOLLAR_QUOTE_URL",
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normaliza el nivel de logging para evitar configuraciones ambiguas."""
        normalized = value.upper()
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed_levels:
            raise ValueError(f"LOG_LEVEL debe ser uno de: {', '.join(sorted(allowed_levels))}")
        return normalized

    @field_validator("external_api_timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        """Evita timeouts nulos o excesivos en integraciones externas."""
        if value < 1 or value > 120:
            raise ValueError("EXTERNAL_API_TIMEOUT_SECONDS debe estar entre 1 y 120")
        return value

    @field_validator("external_api_dollar_quote_url")
    @classmethod
    def validate_external_api_url(cls, value: str) -> str:
        """Valida URLs HTTP configuradas para integraciones externas."""
        if not value.startswith(("https://", "http://")):
            raise ValueError("EXTERNAL_API_DOLLAR_QUOTE_URL debe ser una URL HTTP o HTTPS")
        return value

    @model_validator(mode="after")
    def validate_real_write_requirements(self) -> "Settings":
        """Exige configuracion minima cuando se desactiva el modo dry-run."""
        if self.dry_run:
            return self

        missing_fields: list[str] = []
        if self.google_application_credentials is None:
            missing_fields.append("GOOGLE_APPLICATION_CREDENTIALS")
        elif not self.google_application_credentials.exists():
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS apunta a un archivo inexistente")

        if not self.google_sheets_spreadsheet_id:
            missing_fields.append("GOOGLE_SHEETS_SPREADSHEET_ID")

        if missing_fields:
            joined_fields = ", ".join(missing_fields)
            raise ValueError(f"Falta configuracion requerida para escritura real: {joined_fields}")

        return self
