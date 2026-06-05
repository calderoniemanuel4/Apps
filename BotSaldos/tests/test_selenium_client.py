from app.core.config import Settings
from app.integrations.selenium_client import SeleniumClient


def test_launch_args_are_parsed() -> None:
    settings = Settings(
        _env_file=None,
        SELENIUM_LAUNCH_ARGS="--disable-http2 --start-maximized",
    )

    assert SeleniumClient(settings)._launch_args() == ["--disable-http2", "--start-maximized"]


def test_configure_headers_uses_cdp() -> None:
    settings = Settings(_env_file=None, SELENIUM_ACCEPT_LANGUAGE="es-AR,es;q=0.9")
    driver = FakeDriver()

    SeleniumClient(settings)._configure_headers(driver)

    assert driver.commands == [
        ("Network.enable", {}),
        ("Network.setExtraHTTPHeaders", {"headers": {"Accept-Language": "es-AR,es;q=0.9"}}),
    ]


class FakeDriver:
    def __init__(self) -> None:
        self.commands: list[tuple[str, dict[str, object]]] = []

    def execute_cdp_cmd(self, command: str, payload: dict[str, object]) -> None:
        self.commands.append((command, payload))
