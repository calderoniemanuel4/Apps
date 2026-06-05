from pathlib import Path

import pytest

from app.core.config import Settings
from app.integrations.web_client import WebClient, WebClientError


def test_has_storage_state_detects_existing_file(tmp_path: Path) -> None:
    storage_state = tmp_path / "storage_state.json"
    storage_state.write_text("{}", encoding="utf-8")
    settings = Settings(_env_file=None, PLAYWRIGHT_STORAGE_STATE_PATH=storage_state)

    assert WebClient(settings).has_storage_state() is True


def test_validate_storage_state_fails_when_file_is_missing(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        PLAYWRIGHT_STORAGE_STATE_PATH=tmp_path / "missing.json",
    )

    with pytest.raises(WebClientError, match="storage state"):
        WebClient(settings).validate_storage_state()


def test_manual_login_requires_headed_browser(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        PLAYWRIGHT_HEADLESS=True,
        PLAYWRIGHT_STORAGE_STATE_PATH=tmp_path / "storage_state.json",
    )

    with pytest.raises(WebClientError, match="PLAYWRIGHT_HEADLESS=false"):
        WebClient(settings).save_storage_state_after_manual_login("https://example.com/login")


def test_context_options_include_browser_like_defaults(tmp_path: Path) -> None:
    storage_state = tmp_path / "storage_state.json"
    settings = Settings(_env_file=None)

    options = WebClient(settings)._context_options(storage_state)

    assert options == {
        "locale": "es-AR",
        "timezone_id": "America/Argentina/Buenos_Aires",
        "viewport": {"width": 1280, "height": 720},
        "extra_http_headers": {"Accept-Language": "es-AR,es;q=0.9,en;q=0.8"},
        "storage_state": str(storage_state),
    }


def test_launch_options_include_configured_channel() -> None:
    settings = Settings(
        _env_file=None,
        PLAYWRIGHT_BROWSER="chromium",
        PLAYWRIGHT_CHANNEL="chrome",
        PLAYWRIGHT_HEADLESS=False,
        PLAYWRIGHT_LAUNCH_ARGS="--disable-http2",
    )

    assert WebClient(settings)._launch_options() == {
        "headless": False,
        "channel": "chrome",
        "args": ["--disable-http2"],
    }
