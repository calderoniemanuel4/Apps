from app.core.config import Settings
from app.integrations.galicia_selenium_client import _galicia_portal_config


def test_galicia_portal_config_uses_three_login_fields() -> None:
    config = _galicia_portal_config(_settings())

    assert config.source == "galicia"
    assert config.input_mode == "human"
    assert config.document_number == "12345678"
    assert config.document_number_selector == "//input[@id='document']"
    assert config.username == "user"
    assert config.password == "password"


def _settings() -> Settings:
    return Settings(
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
