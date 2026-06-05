"""Diagnostico de login Santander usando Selenium y Chrome visible."""

from __future__ import annotations

import json
import re
import time
from hashlib import sha256
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.integrations.selenium_client import SeleniumClient

SECRET_FIELD_NAMES = ("password", "pass", "clave", "token", "authorization")
SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-auth-token",
    "x-xsrf-token",
    "x-csrf-token",
}
HEADER_VALUE_ALLOWLIST = {
    "accept",
    "accept-language",
    "content-type",
    "origin",
    "referer",
    "sec-fetch-dest",
    "sec-fetch-mode",
    "sec-fetch-site",
    "user-agent",
}


def main() -> None:
    """Prueba login Santander con Selenium sin escribir en Sheets."""
    settings = Settings()
    configure_logging(settings)

    with SeleniumClient(settings).page() as driver:
        report_started_at = datetime.now(UTC)
        driver.get(settings.santander_login_url)
        wait = WebDriverWait(driver, settings.selenium_page_load_timeout_ms / 1_000)
        before_submit = _capture_page_state(driver, settings, "before_submit")
        _clear_driver_logs(driver)
        submit_strategy = _fill_login(driver, wait, settings)
        _wait_for_home(driver, settings)
        report = save_diagnostic_report(
            driver=driver,
            settings=settings,
            started_at=report_started_at,
            submit_strategy=submit_strategy,
            before_submit=before_submit,
            after_stage="after_submit",
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
            try:
                _check_balance_xpath(driver, wait, settings)
            finally:
                logout_completed = _logout(driver, wait, settings)
                print(f"logout_completed: {'yes' if logout_completed else 'no'}")
        else:
            print("home_url_reached: no")


def save_diagnostic_report(
    driver: object,
    settings: Settings,
    started_at: datetime,
    submit_strategy: str,
    before_submit: dict[str, object],
    after_stage: str,
) -> dict[str, object]:
    """Guarda un reporte Selenium sanitizado y devuelve sus rutas y resumen."""
    after_submit = _capture_page_state(driver, settings, after_stage)
    network_events = _collect_network_events(driver)
    response_bodies = _collect_response_bodies(driver, network_events)
    browser_logs = _collect_browser_logs(driver)
    screenshot_path = _save_screenshot(driver)
    report_payload = {
        "started_at": started_at.isoformat(),
        "submit_strategy": submit_strategy,
        "home_url_reached": driver.current_url == settings.santander_post_login_url,
        "before_submit": before_submit,
        "after_submit": after_submit,
        "network_events": network_events,
        "response_bodies": response_bodies,
        "browser_logs": browser_logs,
        "screenshot": str(screenshot_path),
    }
    report_path = _save_report(report_payload)
    return {
        **report_payload,
        "report_path": str(report_path),
    }


def _fill_login(driver: object, wait: WebDriverWait, settings: Settings) -> str:
    user_input = wait.until(
        ec.visibility_of_element_located((By.XPATH, settings.santander_username_selector))
    )
    password_input = wait.until(
        ec.visibility_of_element_located((By.XPATH, settings.santander_password_selector))
    )
    if settings.santander_input_mode == "human":
        _fill_login_human_like(driver, wait, settings, user_input, password_input)
        return f"human_{settings.santander_submit_strategy}"

    user_input.clear()
    user_input.send_keys(settings.santander_username)
    password_input.clear()
    password_input.send_keys(settings.santander_password)
    if settings.santander_submit_strategy == "enter":
        password_input.submit()
        return "enter"

    submit_button = wait.until(
        ec.element_to_be_clickable((By.XPATH, settings.santander_submit_selector))
    )
    submit_button.click()
    return "click"


def _fill_login_human_like(
    driver: object,
    wait: WebDriverWait,
    settings: Settings,
    user_input: object,
    password_input: object,
) -> None:
    delay_seconds = settings.santander_type_delay_ms / 1_000
    _click_and_type_human_like(driver, user_input, settings.santander_username, delay_seconds)
    time.sleep(max(delay_seconds * 2, 0.12))
    _click_and_type_human_like(driver, password_input, settings.santander_password, delay_seconds)
    time.sleep(max(delay_seconds * 4, 0.25))

    if settings.santander_submit_strategy == "enter":
        password_input.send_keys("\n")
        return

    submit_button = wait.until(
        ec.element_to_be_clickable((By.XPATH, settings.santander_submit_selector))
    )
    ActionChains(driver).move_to_element(submit_button).pause(0.2).click().perform()


def _click_and_type_human_like(
    driver: object,
    element: object,
    value: str | None,
    delay_seconds: float,
) -> None:
    if value is None:
        raise ValueError("Falta valor para completar login.")

    ActionChains(driver).move_to_element(element).pause(0.15).click().perform()
    element.clear()
    for character in value:
        element.send_keys(character)
        time.sleep(delay_seconds)


def _wait_for_home(driver: object, settings: Settings) -> None:
    wait = WebDriverWait(driver, settings.selenium_page_load_timeout_ms / 1_000)
    try:
        wait.until(
            lambda current_driver: current_driver.current_url == settings.santander_post_login_url
        )
    except TimeoutException:
        return


def _check_balance_xpath(driver: object, wait: WebDriverWait, settings: Settings) -> None:
    try:
        balance_element = wait.until(
            ec.visibility_of_element_located((By.XPATH, settings.santander_balance_xpath))
        )
        print(f"balance_xpath_found: {'yes' if balance_element.text.strip() else 'empty'}")
    except TimeoutException:
        print("balance_xpath_found: no")


def _logout(driver: object, wait: WebDriverWait, settings: Settings) -> bool:
    try:
        logout_button = wait.until(
            ec.element_to_be_clickable((By.XPATH, settings.santander_logout_selector))
        )
        ActionChains(driver).move_to_element(logout_button).pause(0.2).click().perform()
        confirm_button = wait.until(
            ec.element_to_be_clickable((By.XPATH, settings.santander_logout_confirm_selector))
        )
        ActionChains(driver).move_to_element(confirm_button).pause(0.2).click().perform()
        wait.until(lambda current_driver: "#!/login" in current_driver.current_url)
        return True
    except TimeoutException:
        return False


def _capture_page_state(driver: object, settings: Settings, stage: str) -> dict[str, object]:
    return {
        "stage": stage,
        "url": driver.current_url,
        "title": driver.title,
        "active_element": _safe_execute_script(driver, _ACTIVE_ELEMENT_SCRIPT),
        "login_form": _safe_execute_script(driver, _login_form_script(settings)),
        "visible_text_summary": _visible_text_summary(driver),
    }


def _safe_execute_script(driver: object, script: str) -> object:
    try:
        return _sanitize_value(driver.execute_script(script))
    except Exception as exc:
        return {"error": _sanitize_text(str(exc))}


def _login_form_script(settings: Settings) -> str:
    selectors = {
        "user": settings.santander_username_selector,
        "password": settings.santander_password_selector,
        "submit": settings.santander_submit_selector,
    }
    return f"""
const selectors = {json.dumps(selectors)};
function byXpath(xpath) {{
  return document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null)
    .singleNodeValue;
}}
function describe(element) {{
  if (!element) return {{ found: false }};
  const rect = element.getBoundingClientRect();
  return {{
    found: true,
    tag: element.tagName,
    type: element.getAttribute("type"),
    id: element.id || null,
    name: element.getAttribute("name"),
    disabled: Boolean(element.disabled),
    ariaDisabled: element.getAttribute("aria-disabled"),
    required: Boolean(element.required),
    readonly: Boolean(element.readOnly),
    valueLength: typeof element.value === "string" ? element.value.length : null,
    textLength: typeof element.innerText === "string" ? element.innerText.length : null,
    classes: element.className || null,
    visible: Boolean(rect.width && rect.height),
    rect: {{ x: rect.x, y: rect.y, width: rect.width, height: rect.height }},
    formAction: element.form ? element.form.getAttribute("action") : null,
    formMethod: element.form ? element.form.getAttribute("method") : null,
    formNoValidate: element.form ? Boolean(element.form.noValidate) : null,
  }};
}}
return {{
  readyState: document.readyState,
  user: describe(byXpath(selectors.user)),
  credential_field: describe(byXpath(selectors.password)),
  submit: describe(byXpath(selectors.submit)),
}};
"""


def _visible_text_summary(driver: object) -> dict[str, object]:
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
    except Exception as exc:
        return {"error": _sanitize_text(str(exc))}

    sanitized = _sanitize_text(body_text)
    interesting_lines = [
        line
        for line in sanitized.splitlines()
        if re.search(r"error|incorrect|clave|contrase|intento|bloque|servicio|valid", line, re.I)
    ]
    return {
        "line_count": len([line for line in sanitized.splitlines() if line.strip()]),
        "interesting_lines": interesting_lines[:20],
    }


def _clear_driver_logs(driver: object) -> None:
    for log_type in ("browser", "performance"):
        try:
            driver.get_log(log_type)
        except Exception:
            continue


def _collect_network_events(driver: object) -> list[dict[str, object]]:
    try:
        raw_entries = driver.get_log("performance")
    except Exception as exc:
        return [{"error": _sanitize_text(str(exc))}]

    events: list[dict[str, object]] = []
    for entry in raw_entries:
        parsed = _parse_performance_entry(entry)
        if parsed is not None:
            events.append(parsed)
    return events[:200]


def _parse_performance_entry(entry: dict[str, Any]) -> dict[str, object] | None:
    try:
        message = json.loads(entry["message"])["message"]
    except Exception:
        return None

    method = message.get("method")
    params = message.get("params", {})
    if method == "Network.requestWillBeSent":
        request = params.get("request", {})
        url = str(request.get("url", ""))
        return {
            "event": "request",
            "request_id": params.get("requestId"),
            "method": request.get("method"),
            "url": _redact_url(url),
            "resource_type": params.get("type"),
            "headers_summary": _summarize_headers(request.get("headers", {})),
            "post_data_summary": _summarize_post_data(request.get("postData")),
        }
    if method == "Network.responseReceived":
        response = params.get("response", {})
        url = str(response.get("url", ""))
        return {
            "event": "response",
            "request_id": params.get("requestId"),
            "status": response.get("status"),
            "url": _redact_url(url),
            "mime_type": response.get("mimeType"),
        }
    if method == "Network.loadingFailed":
        return {
            "event": "failed",
            "error_text": _sanitize_text(str(params.get("errorText"))),
            "blocked_reason": params.get("blockedReason"),
            "resource_type": params.get("type"),
        }
    return None


def _collect_browser_logs(driver: object) -> list[dict[str, object]]:
    try:
        raw_logs = driver.get_log("browser")
    except Exception as exc:
        return [{"error": _sanitize_text(str(exc))}]

    return [
        {
            "level": log.get("level"),
            "message": _sanitize_text(str(log.get("message"))),
        }
        for log in raw_logs[:100]
    ]


def _summarize_headers(headers: object) -> dict[str, object]:
    if not isinstance(headers, dict):
        return {"names": [], "values": {}}

    names = sorted(str(name).lower() for name in headers)
    values: dict[str, object] = {}
    for name, value in headers.items():
        normalized_name = str(name).lower()
        if normalized_name in SENSITIVE_HEADER_NAMES:
            values[normalized_name] = "<redacted>"
        elif normalized_name in HEADER_VALUE_ALLOWLIST:
            values[normalized_name] = _sanitize_text(str(value))
    return {
        "names": names,
        "values": values,
    }


def _summarize_post_data(post_data: object) -> dict[str, object] | None:
    if post_data is None:
        return None

    text = str(post_data)
    summary: dict[str, object] = {
        "length": len(text),
        "sha256": sha256(text.encode("utf-8")).hexdigest(),
    }
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return summary

    if isinstance(parsed, dict):
        summary["json_keys"] = sorted(str(key) for key in parsed.keys())
        summary["json_shape"] = _json_shape(parsed)
    return summary


def _json_shape(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_shape(value[0])] if value else []
    return type(value).__name__


def _collect_response_bodies(
    driver: object, network_events: list[dict[str, object]]
) -> list[dict[str, object]]:
    selected_events = [
        event
        for event in network_events
        if event.get("event") == "response"
        and event.get("request_id")
        and _should_capture_response_body(str(event.get("url", "")))
    ]

    bodies: list[dict[str, object]] = []
    for event in selected_events[:10]:
        try:
            response_body = driver.execute_cdp_cmd(
                "Network.getResponseBody",
                {"requestId": event["request_id"]},
            )
            bodies.append(
                {
                    "url": event.get("url"),
                    "status": event.get("status"),
                    "base64_encoded": response_body.get("base64Encoded"),
                    "body": _sanitize_response_body(str(response_body.get("body", ""))),
                }
            )
        except Exception as exc:
            bodies.append(
                {
                    "url": event.get("url"),
                    "status": event.get("status"),
                    "error": _sanitize_text(str(exc)),
                }
            )
    return bodies


def _should_capture_response_body(url: str) -> bool:
    return (
        "www2.personas.santander.com.ar/obp-servicios/login/doLogin" in url
        or "www2.personas.santander.com.ar/obp-servicios/inicial/doInit" in url
    )


def _sanitize_response_body(body: str) -> object:
    try:
        return _sanitize_value(json.loads(body))
    except json.JSONDecodeError:
        return _sanitize_text(body)


def _save_screenshot(driver: object) -> Path:
    screenshot_dir = Path("tmp")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    screenshot_path = screenshot_dir / f"santander_selenium_{timestamp}.png"
    driver.save_screenshot(str(screenshot_path))
    return screenshot_path


def _save_report(report: dict[str, object]) -> Path:
    report_dir = Path("tmp")
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = report_dir / f"santander_selenium_report_{timestamp}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def _redact_url(url: str) -> str:
    split_url = urlsplit(url)
    redacted = split_url._replace(query="<redacted>" if split_url.query else "")
    return redacted.geturl()


def _sanitize_value(value: object) -> object:
    if isinstance(value, dict):
        sanitized: dict[str, object] = {}
        for key, item in value.items():
            if any(secret in str(key).lower() for secret in SECRET_FIELD_NAMES):
                sanitized[str(key)] = "<redacted>"
            else:
                sanitized[str(key)] = _sanitize_value(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _sanitize_text(value: str) -> str:
    sanitized = re.sub(r"\b\d{4,}\b", "<number>", value)
    if len(sanitized) > 1_000:
        return f"{sanitized[:1_000]}..."
    return sanitized


_ACTIVE_ELEMENT_SCRIPT = """
const element = document.activeElement;
if (!element) return null;
const rect = element.getBoundingClientRect();
return {
  tag: element.tagName,
  type: element.getAttribute("type"),
  id: element.id || null,
  name: element.getAttribute("name"),
  classes: element.className || null,
  valueLength: typeof element.value === "string" ? element.value.length : null,
  textLength: typeof element.innerText === "string" ? element.innerText.length : null,
  rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
};
"""


if __name__ == "__main__":
    main()
