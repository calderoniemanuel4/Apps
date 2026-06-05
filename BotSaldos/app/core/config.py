"""Configuracion centralizada de BotSaldos."""

import shlex
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
    playwright_browser: str = Field(default="chromium", alias="PLAYWRIGHT_BROWSER")
    playwright_channel: str | None = Field(default=None, alias="PLAYWRIGHT_CHANNEL")
    playwright_launch_args: str | None = Field(default=None, alias="PLAYWRIGHT_LAUNCH_ARGS")
    playwright_storage_state_path: Path = Field(
        default=Path("playwright/.auth/storage_state.json"),
        alias="PLAYWRIGHT_STORAGE_STATE_PATH",
    )
    playwright_default_timeout_ms: int = Field(
        default=30_000,
        alias="PLAYWRIGHT_DEFAULT_TIMEOUT_MS",
    )
    playwright_locale: str = Field(default="es-AR", alias="PLAYWRIGHT_LOCALE")
    playwright_timezone_id: str = Field(
        default="America/Argentina/Buenos_Aires",
        alias="PLAYWRIGHT_TIMEZONE_ID",
    )
    playwright_viewport_width: int = Field(default=1280, alias="PLAYWRIGHT_VIEWPORT_WIDTH")
    playwright_viewport_height: int = Field(default=720, alias="PLAYWRIGHT_VIEWPORT_HEIGHT")
    playwright_accept_language: str = Field(
        default="es-AR,es;q=0.9,en;q=0.8",
        alias="PLAYWRIGHT_ACCEPT_LANGUAGE",
    )
    selenium_headless: bool = Field(default=False, alias="SELENIUM_HEADLESS")
    selenium_page_load_timeout_ms: int = Field(
        default=30_000,
        alias="SELENIUM_PAGE_LOAD_TIMEOUT_MS",
    )
    selenium_window_width: int = Field(default=1280, alias="SELENIUM_WINDOW_WIDTH")
    selenium_window_height: int = Field(default=720, alias="SELENIUM_WINDOW_HEIGHT")
    selenium_accept_language: str = Field(
        default="es-AR,es;q=0.9,en;q=0.8",
        alias="SELENIUM_ACCEPT_LANGUAGE",
    )
    selenium_user_agent: str | None = Field(default=None, alias="SELENIUM_USER_AGENT")
    selenium_launch_args: str | None = Field(
        default="--disable-http2",
        alias="SELENIUM_LAUNCH_ARGS",
    )
    santander_enabled: bool = Field(default=False, alias="SANTANDER_ENABLED")
    santander_login_url: str = Field(
        default="https://www2.personas.santander.com.ar/obp-webapp/angular/#!/login",
        alias="SANTANDER_LOGIN_URL",
    )
    santander_post_login_url: str = Field(
        default="https://www2.personas.santander.com.ar/obp-webapp/angular/#!/home",
        alias="SANTANDER_POST_LOGIN_URL",
    )
    santander_web_driver: str = Field(default="playwright", alias="SANTANDER_WEB_DRIVER")
    santander_username: str | None = Field(default=None, alias="SANTANDER_USERNAME")
    santander_password: str | None = Field(default=None, alias="SANTANDER_PASSWORD")
    santander_username_selector: str | None = Field(
        default=None,
        alias="SANTANDER_USERNAME_SELECTOR",
    )
    santander_password_selector: str | None = Field(
        default=None,
        alias="SANTANDER_PASSWORD_SELECTOR",
    )
    santander_submit_selector: str | None = Field(
        default=None,
        alias="SANTANDER_SUBMIT_SELECTOR",
    )
    santander_input_mode: str = Field(default="direct", alias="SANTANDER_INPUT_MODE")
    santander_submit_strategy: str = Field(default="click", alias="SANTANDER_SUBMIT_STRATEGY")
    santander_type_delay_ms: int = Field(default=60, alias="SANTANDER_TYPE_DELAY_MS")
    santander_balance_xpath: str | None = Field(default=None, alias="SANTANDER_BALANCE_XPATH")
    santander_logout_selector: str | None = Field(default=None, alias="SANTANDER_LOGOUT_SELECTOR")
    santander_logout_confirm_selector: str | None = Field(
        default=None,
        alias="SANTANDER_LOGOUT_CONFIRM_SELECTOR",
    )
    santander_login_error_selector: str | None = Field(
        default=None,
        alias="SANTANDER_LOGIN_ERROR_SELECTOR",
    )
    santander_offline_selector: str | None = Field(
        default=None,
        alias="SANTANDER_OFFLINE_SELECTOR",
    )
    santander_max_login_attempts: int = Field(default=2, alias="SANTANDER_MAX_LOGIN_ATTEMPTS")
    santander_attempt_state_file: Path = Field(
        default=Path("tmp/santander_login_attempts.json"),
        alias="SANTANDER_ATTEMPT_STATE_FILE",
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

    @field_validator("playwright_default_timeout_ms")
    @classmethod
    def validate_playwright_timeout(cls, value: int) -> int:
        """Evita timeouts de Playwright demasiado agresivos o excesivos."""
        if value < 1_000 or value > 120_000:
            raise ValueError("PLAYWRIGHT_DEFAULT_TIMEOUT_MS debe estar entre 1000 y 120000")
        return value

    @field_validator("playwright_browser")
    @classmethod
    def validate_playwright_browser(cls, value: str) -> str:
        """Valida el motor de navegador usado por Playwright."""
        normalized = value.lower()
        allowed_browsers = {"chromium", "firefox", "webkit"}
        if normalized not in allowed_browsers:
            raise ValueError(
                f"PLAYWRIGHT_BROWSER debe ser uno de: {', '.join(sorted(allowed_browsers))}"
            )
        return normalized

    @field_validator("playwright_channel", mode="before")
    @classmethod
    def normalize_playwright_channel(cls, value: str | None) -> str | None:
        """Normaliza el canal del navegador Playwright."""
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if not normalized:
            return None
        allowed_channels = {
            "chrome",
            "chrome-beta",
            "chrome-dev",
            "chrome-canary",
            "msedge",
            "msedge-beta",
            "msedge-dev",
            "msedge-canary",
        }
        if normalized not in allowed_channels:
            raise ValueError(
                f"PLAYWRIGHT_CHANNEL debe ser uno de: {', '.join(sorted(allowed_channels))}"
            )
        return normalized

    @field_validator("playwright_launch_args", mode="before")
    @classmethod
    def normalize_playwright_launch_args(cls, value: str | None) -> str | None:
        """Normaliza flags opcionales de lanzamiento Playwright."""
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        parsed_args = shlex.split(normalized)
        if any(not arg.startswith("--") for arg in parsed_args):
            raise ValueError("PLAYWRIGHT_LAUNCH_ARGS solo acepta flags que empiecen con --")
        return " ".join(parsed_args)

    @field_validator("playwright_viewport_width", "playwright_viewport_height")
    @classmethod
    def validate_playwright_viewport(cls, value: int) -> int:
        """Evita viewports nulos o extremos en automatizaciones web."""
        if value < 320 or value > 4_096:
            raise ValueError("Las dimensiones de viewport Playwright deben estar entre 320 y 4096")
        return value

    @field_validator("playwright_locale", "playwright_timezone_id", "playwright_accept_language")
    @classmethod
    def validate_playwright_context_text(cls, value: str) -> str:
        """Evita valores vacios para el contexto Playwright."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("La configuracion de contexto Playwright no puede estar vacia")
        return normalized

    @field_validator("selenium_page_load_timeout_ms")
    @classmethod
    def validate_selenium_page_load_timeout(cls, value: int) -> int:
        """Evita timeouts de Selenium demasiado agresivos o excesivos."""
        if value < 1_000 or value > 120_000:
            raise ValueError("SELENIUM_PAGE_LOAD_TIMEOUT_MS debe estar entre 1000 y 120000")
        return value

    @field_validator("selenium_window_width", "selenium_window_height")
    @classmethod
    def validate_selenium_window_size(cls, value: int) -> int:
        """Evita ventanas Selenium nulas o extremas."""
        if value < 320 or value > 4_096:
            raise ValueError("Las dimensiones de ventana Selenium deben estar entre 320 y 4096")
        return value

    @field_validator("selenium_accept_language")
    @classmethod
    def validate_selenium_accept_language(cls, value: str) -> str:
        """Evita headers vacios para Selenium."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("SELENIUM_ACCEPT_LANGUAGE no puede estar vacio")
        return normalized

    @field_validator("selenium_user_agent", mode="before")
    @classmethod
    def normalize_selenium_user_agent(cls, value: str | None) -> str | None:
        """Normaliza User-Agent opcional de Selenium."""
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("selenium_launch_args", mode="before")
    @classmethod
    def normalize_selenium_launch_args(cls, value: str | None) -> str | None:
        """Normaliza flags opcionales de Chrome para Selenium."""
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        parsed_args = shlex.split(normalized)
        if any(not arg.startswith("--") for arg in parsed_args):
            raise ValueError("SELENIUM_LAUNCH_ARGS solo acepta flags que empiecen con --")
        return " ".join(parsed_args)

    @field_validator("santander_login_url", "santander_post_login_url")
    @classmethod
    def validate_santander_login_url(cls, value: str) -> str:
        """Valida URLs de Santander."""
        if not value.startswith(("https://", "http://")):
            raise ValueError("Las URLs de Santander deben ser HTTP o HTTPS")
        return value

    @field_validator("santander_web_driver")
    @classmethod
    def validate_santander_web_driver(cls, value: str) -> str:
        """Valida el motor web usado por Santander."""
        normalized = value.lower()
        allowed_drivers = {"playwright", "selenium"}
        if normalized not in allowed_drivers:
            raise ValueError(
                f"SANTANDER_WEB_DRIVER debe ser uno de: {', '.join(sorted(allowed_drivers))}"
            )
        return normalized

    @field_validator("santander_max_login_attempts")
    @classmethod
    def validate_santander_attempts(cls, value: int) -> int:
        """Evita limites de intentos nulos o excesivos."""
        if value < 1 or value > 10:
            raise ValueError("SANTANDER_MAX_LOGIN_ATTEMPTS debe estar entre 1 y 10")
        return value

    @field_validator("santander_type_delay_ms")
    @classmethod
    def validate_santander_type_delay(cls, value: int) -> int:
        """Evita demoras de tipeo negativas o excesivas."""
        if value < 0 or value > 1_000:
            raise ValueError("SANTANDER_TYPE_DELAY_MS debe estar entre 0 y 1000")
        return value

    @field_validator("santander_submit_strategy")
    @classmethod
    def validate_santander_submit_strategy(cls, value: str) -> str:
        """Valida la forma de enviar el login."""
        normalized = value.lower()
        allowed_strategies = {"click", "enter"}
        if normalized not in allowed_strategies:
            raise ValueError(
                "SANTANDER_SUBMIT_STRATEGY debe ser uno de: "
                f"{', '.join(sorted(allowed_strategies))}"
            )
        return normalized

    @field_validator("santander_input_mode")
    @classmethod
    def validate_santander_input_mode(cls, value: str) -> str:
        """Valida el modo de ingreso de credenciales."""
        normalized = value.lower()
        allowed_modes = {"direct", "human"}
        if normalized not in allowed_modes:
            raise ValueError(
                f"SANTANDER_INPUT_MODE debe ser uno de: {', '.join(sorted(allowed_modes))}"
            )
        return normalized

    @model_validator(mode="after")
    def validate_playwright_channel_requirements(self) -> "Settings":
        """Evita combinar canales Chromium con motores incompatibles."""
        if self.playwright_channel is not None and self.playwright_browser != "chromium":
            raise ValueError("PLAYWRIGHT_CHANNEL solo puede usarse con PLAYWRIGHT_BROWSER=chromium")
        return self

    @model_validator(mode="after")
    def validate_santander_requirements(self) -> "Settings":
        """Exige configuracion minima cuando Santander esta habilitado."""
        if not self.santander_enabled:
            return self

        missing_fields: list[str] = []
        required_values = {
            "SANTANDER_USERNAME": self.santander_username,
            "SANTANDER_PASSWORD": self.santander_password,
            "SANTANDER_USERNAME_SELECTOR": self.santander_username_selector,
            "SANTANDER_PASSWORD_SELECTOR": self.santander_password_selector,
            "SANTANDER_SUBMIT_SELECTOR": self.santander_submit_selector,
            "SANTANDER_BALANCE_XPATH": self.santander_balance_xpath,
            "SANTANDER_LOGOUT_SELECTOR": self.santander_logout_selector,
            "SANTANDER_LOGOUT_CONFIRM_SELECTOR": self.santander_logout_confirm_selector,
        }
        for field_name, field_value in required_values.items():
            if not field_value:
                missing_fields.append(field_name)

        if missing_fields:
            joined_fields = ", ".join(missing_fields)
            raise ValueError(f"Falta configuracion requerida para Santander: {joined_fields}")

        return self

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
