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
    assert settings.balance_state_file == Path("tmp/balances.json")
    assert settings.google_sheets_spreadsheet_id is None
    assert settings.google_sheets_worksheet_name == "Cotizaciones"
    assert settings.external_api_dollar_quote_url == "https://dolarapi.com/v1/dolares/oficial"
    assert settings.selenium_headless is False
    assert settings.selenium_page_load_timeout_ms == 30_000
    assert settings.selenium_window_width == 1280
    assert settings.selenium_window_height == 720
    assert settings.selenium_accept_language == "es-AR,es;q=0.9,en;q=0.8"
    assert settings.selenium_user_agent is None
    assert settings.selenium_launch_args == "--disable-http2"
    assert settings.santander_enabled is False
    assert settings.santander_max_login_attempts == 2
    assert settings.santander_input_mode == "direct"
    assert settings.santander_submit_strategy == "click"
    assert settings.santander_type_delay_ms == 60
    assert settings.santander_logout_success_url is None
    assert settings.santander_logout_timeout_ms == 3_000
    assert settings.santander_post_login_url.endswith("#!/home")
    assert settings.galicia_enabled is False
    assert settings.galicia_login_url == ""
    assert settings.galicia_input_mode == "human"
    assert settings.galicia_submit_strategy == "click"
    assert settings.galicia_type_delay_ms == 60
    assert settings.galicia_attempt_state_file == Path("tmp/galicia_login_attempts.json")
    assert settings.mercadopago_enabled is False
    assert settings.mercadopago_release_report_url.endswith("/v1/account/release_report")
    assert settings.mercadopago_release_report_config_url.endswith(
        "/v1/account/release_report/config"
    )
    assert settings.mercadopago_report_wait_seconds == 30
    assert settings.mercadopago_report_max_attempts == 5
    assert settings.mercadopago_configure_report is True
    assert settings.mercadopago_report_display_timezone == "GMT-03"
    assert settings.mercadopago_report_state_file == Path("tmp/mercadopago_release_reports.json")


def test_real_write_requires_google_sheets_configuration() -> None:
    with pytest.raises(ValidationError, match="Falta configuracion requerida"):
        Settings(_env_file=None, DRY_RUN=False)


def test_invalid_log_level_fails_fast() -> None:
    with pytest.raises(ValidationError, match="LOG_LEVEL"):
        Settings(_env_file=None, LOG_LEVEL="VERBOSE")


def test_external_api_url_accepts_configured_http_url() -> None:
    settings = Settings(
        _env_file=None,
        EXTERNAL_API_DOLLAR_QUOTE_URL="https://example.com/dolar",
    )

    assert settings.external_api_dollar_quote_url == "https://example.com/dolar"


def test_external_api_url_requires_http_scheme() -> None:
    with pytest.raises(ValidationError, match="EXTERNAL_API_DOLLAR_QUOTE_URL"):
        Settings(_env_file=None, EXTERNAL_API_DOLLAR_QUOTE_URL="ftp://example.com/feed")


def test_invalid_selenium_timeout_fails_fast() -> None:
    with pytest.raises(ValidationError, match="SELENIUM_PAGE_LOAD_TIMEOUT_MS"):
        Settings(_env_file=None, SELENIUM_PAGE_LOAD_TIMEOUT_MS=500)


def test_invalid_selenium_window_size_fails_fast() -> None:
    with pytest.raises(ValidationError, match="ventana Selenium"):
        Settings(_env_file=None, SELENIUM_WINDOW_WIDTH=100)


def test_selenium_launch_args_requires_flags() -> None:
    with pytest.raises(ValidationError, match="SELENIUM_LAUNCH_ARGS"):
        Settings(_env_file=None, SELENIUM_LAUNCH_ARGS="disable-http2")


def test_santander_enabled_requires_configuration() -> None:
    with pytest.raises(ValidationError, match="Falta configuracion requerida para Santander"):
        Settings(_env_file=None, SANTANDER_ENABLED=True)


def test_galicia_enabled_requires_configuration() -> None:
    with pytest.raises(ValidationError, match="Falta configuracion requerida para Galicia"):
        Settings(_env_file=None, GALICIA_ENABLED=True)


def test_galicia_enabled_accepts_required_configuration() -> None:
    settings = Settings(
        _env_file=None,
        GALICIA_ENABLED=True,
        GALICIA_LOGIN_URL="https://example.com/login",
        GALICIA_POST_LOGIN_URL="https://example.com/home",
        GALICIA_DOCUMENT_NUMBER="12345678",
        GALICIA_DOCUMENT_NUMBER_SELECTOR="//input[@id='document']",
        GALICIA_USERNAME="user",
        GALICIA_PASSWORD="password",
        GALICIA_USERNAME_SELECTOR="//input[@id='user']",
        GALICIA_PASSWORD_SELECTOR="//input[@id='password']",
        GALICIA_SUBMIT_SELECTOR="//button[@type='submit']",
        GALICIA_BALANCE_XPATH="//span[@id='balance']",
        GALICIA_LOGOUT_SELECTOR="//a[@id='logout']",
    )

    assert settings.galicia_enabled is True


def test_mercadopago_enabled_requires_access_token() -> None:
    with pytest.raises(ValidationError, match="Falta configuracion requerida para Mercado Pago"):
        Settings(_env_file=None, MERCADOPAGO_ENABLED=True)


def test_mercadopago_enabled_accepts_required_configuration() -> None:
    settings = Settings(
        _env_file=None,
        MERCADOPAGO_ENABLED=True,
        MERCADOPAGO_ACCESS_TOKEN="token",
    )

    assert settings.mercadopago_enabled is True


def test_mercadopago_report_wait_is_bounded() -> None:
    with pytest.raises(ValidationError, match="MERCADOPAGO_REPORT_WAIT_SECONDS"):
        Settings(_env_file=None, MERCADOPAGO_REPORT_WAIT_SECONDS=-1)


def test_mercadopago_report_max_attempts_is_bounded() -> None:
    with pytest.raises(ValidationError, match="MERCADOPAGO_REPORT_MAX_ATTEMPTS"):
        Settings(_env_file=None, MERCADOPAGO_REPORT_MAX_ATTEMPTS=0)


def test_mercadopago_report_display_timezone_is_required() -> None:
    with pytest.raises(ValidationError, match="MERCADOPAGO_REPORT_DISPLAY_TIMEZONE"):
        Settings(_env_file=None, MERCADOPAGO_REPORT_DISPLAY_TIMEZONE=" ")


def test_santander_attempt_limit_is_bounded() -> None:
    with pytest.raises(ValidationError, match="intentos de login"):
        Settings(_env_file=None, SANTANDER_MAX_LOGIN_ATTEMPTS=0)


def test_santander_logout_timeout_is_bounded() -> None:
    with pytest.raises(ValidationError, match="timeout de logout"):
        Settings(_env_file=None, SANTANDER_LOGOUT_TIMEOUT_MS=100)


def test_santander_logout_success_url_requires_http() -> None:
    with pytest.raises(ValidationError, match="URL de logout"):
        Settings(_env_file=None, SANTANDER_LOGOUT_SUCCESS_URL="ftp://example.com/logout")


def test_santander_type_delay_is_bounded() -> None:
    with pytest.raises(ValidationError, match="demora de tipeo"):
        Settings(_env_file=None, SANTANDER_TYPE_DELAY_MS=-1)


def test_santander_submit_strategy_is_bounded() -> None:
    with pytest.raises(ValidationError, match="estrategia de submit"):
        Settings(_env_file=None, SANTANDER_SUBMIT_STRATEGY="double_click")


def test_santander_input_mode_is_bounded() -> None:
    with pytest.raises(ValidationError, match="modo de ingreso"):
        Settings(_env_file=None, SANTANDER_INPUT_MODE="robot")
