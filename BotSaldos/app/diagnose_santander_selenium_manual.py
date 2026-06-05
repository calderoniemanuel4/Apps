"""Diagnostico comparativo con login manual en Chrome Selenium."""

from __future__ import annotations

from datetime import UTC, datetime

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.diagnose_santander_selenium import (
    _capture_page_state,
    _check_balance_xpath,
    _clear_driver_logs,
    save_diagnostic_report,
)
from app.integrations.selenium_client import SeleniumClient


def main() -> None:
    """Abre Santander y espera que el usuario haga login manualmente."""
    settings = Settings()
    configure_logging(settings)

    with SeleniumClient(settings).page() as driver:
        started_at = datetime.now(UTC)
        driver.get(settings.santander_login_url)
        before_submit = _capture_page_state(driver, settings, "before_manual_login")
        _clear_driver_logs(driver)
        print("Chrome esta abierto. Completa el login manualmente en la ventana.")
        print("No cierres la ventana antes de capturar el diagnostico.")
        input("Cuando termines o veas el resultado, presiona Enter aca para capturar diagnostico...")
        if not _switch_to_open_window(driver):
            print("No se pudo capturar: la ventana de Chrome fue cerrada.")
            return
        wait = WebDriverWait(driver, settings.selenium_page_load_timeout_ms / 1_000)
        report = save_diagnostic_report(
            driver=driver,
            settings=settings,
            started_at=started_at,
            submit_strategy="manual",
            before_submit=before_submit,
            after_stage="after_manual_login",
        )
        print(f"current_url: {driver.current_url}")
        print(f"title: {driver.title}")
        print(f"screenshot: {report['screenshot']}")
        print(f"diagnostic_report: {report['report_path']}")
        print(f"network_event_count: {len(report['network_events'])}")
        print(f"response_body_count: {len(report['response_bodies'])}")
        print(f"browser_log_count: {len(report['browser_logs'])}")
        if driver.current_url == settings.santander_post_login_url:
            print("home_url_reached: yes")
            _check_balance_xpath(driver, wait, settings)
        else:
            print("home_url_reached: no")


def _switch_to_open_window(driver: object) -> bool:
    try:
        handles = driver.window_handles
        if not handles:
            return False
        driver.switch_to.window(handles[-1])
        return True
    except WebDriverException:
        return False


if __name__ == "__main__":
    main()
