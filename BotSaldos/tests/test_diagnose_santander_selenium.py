import json

from app.diagnose_santander_selenium import (
    _collect_response_bodies,
    _parse_performance_entry,
    _redact_url,
    _summarize_headers,
    _summarize_post_data,
    _sanitize_response_body,
    _sanitize_value,
)


def test_redact_url_removes_query_string() -> None:
    assert _redact_url("https://example.com/login?token=abc") == "https://example.com/login?<redacted>"


def test_sanitize_value_redacts_secret_keys() -> None:
    value = {"password": "secret", "nested": {"token": "abc", "safe": "ok"}}

    assert _sanitize_value(value) == {
        "password": "<redacted>",
        "nested": {"token": "<redacted>", "safe": "ok"},
    }


def test_parse_performance_entry_summarizes_request_without_query() -> None:
    entry = {
        "message": json.dumps(
            {
                "message": {
                    "method": "Network.requestWillBeSent",
                    "params": {
                        "requestId": "123",
                        "type": "XHR",
                        "request": {
                            "method": "POST",
                            "url": "https://www2.personas.santander.com.ar/login?secret=1",
                            "headers": {"Content-Type": "application/json", "Cookie": "secret"},
                            "postData": '{"usuario":"x","clave":"y"}',
                        },
                    },
                }
            }
        )
    }

    assert _parse_performance_entry(entry) == {
        "event": "request",
        "request_id": "123",
        "method": "POST",
        "url": "https://www2.personas.santander.com.ar/login?<redacted>",
        "resource_type": "XHR",
        "headers_summary": {
            "names": ["content-type", "cookie"],
            "values": {"content-type": "application/json", "cookie": "<redacted>"},
        },
        "post_data_summary": {
            "length": 27,
            "sha256": "b3acb21c7c4073ec8fd82dcc3fd42ae3a948673dc7cc3e331ae9c42e92591080",
            "json_keys": ["clave", "usuario"],
            "json_shape": {"usuario": "str", "clave": "str"},
        },
    }


def test_summarize_headers_redacts_sensitive_values() -> None:
    assert _summarize_headers({"Cookie": "abc", "Accept": "application/json"}) == {
        "names": ["accept", "cookie"],
        "values": {"accept": "application/json", "cookie": "<redacted>"},
    }


def test_summarize_post_data_does_not_return_raw_body() -> None:
    summary = _summarize_post_data('{"token":"secret","items":[1]}')

    assert summary == {
        "length": 30,
        "sha256": "fcbd6663d0b888b7c0fd55b9c66cf57b06436f6ee4f5f863821600509133c282",
        "json_keys": ["items", "token"],
        "json_shape": {"token": "str", "items": ["int"]},
    }


def test_sanitize_response_body_parses_json() -> None:
    assert _sanitize_response_body('{"status":"ERROR","token":"abc"}') == {
        "status": "ERROR",
        "token": "<redacted>",
    }


def test_collect_response_bodies_reads_selected_santander_response() -> None:
    driver = FakeDriver()
    events = [
        {
            "event": "response",
            "request_id": "abc",
            "status": 200,
            "url": "https://www2.personas.santander.com.ar/obp-servicios/login/doLogin",
        }
    ]

    assert _collect_response_bodies(driver, events) == [
        {
            "url": "https://www2.personas.santander.com.ar/obp-servicios/login/doLogin",
            "status": 200,
            "base64_encoded": False,
            "body": {"status": "ERROR"},
        }
    ]


class FakeDriver:
    def execute_cdp_cmd(self, command: str, payload: dict[str, object]) -> dict[str, object]:
        assert command == "Network.getResponseBody"
        assert payload == {"requestId": "abc"}
        return {"base64Encoded": False, "body": '{"status":"ERROR"}'}
