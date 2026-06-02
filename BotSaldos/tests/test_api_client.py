import httpx
import pytest

from app.core.config import Settings
from app.integrations.api_client import ExternalApiClient, ExternalApiClientError


def test_fetch_dollar_quote_returns_raw_payload_when_quote_value_exists() -> None:
    payload = _dollar_quote_payload()
    http_client = _mock_client(json_payload=payload)
    settings = Settings(_env_file=None)
    client = ExternalApiClient(settings=settings, http_client=http_client)

    quote = client.fetch_dollar_quote()

    assert quote == payload


def test_fetch_dollar_quote_accepts_compra_when_venta_is_missing() -> None:
    payload = {"compra": 1410, "casa": "oficial"}
    http_client = _mock_client(json_payload=payload)
    settings = Settings(_env_file=None)
    client = ExternalApiClient(settings=settings, http_client=http_client)

    quote = client.fetch_dollar_quote()

    assert quote == payload


def test_fetch_dollar_quote_rejects_payload_without_quote_value() -> None:
    http_client = _mock_client(json_payload={"casa": "oficial"})
    settings = Settings(_env_file=None)
    client = ExternalApiClient(settings=settings, http_client=http_client)

    with pytest.raises(ExternalApiClientError, match="cotizacion"):
        client.fetch_dollar_quote()


def test_fetch_dollar_quote_rejects_boolean_quote_value() -> None:
    http_client = _mock_client(json_payload={"venta": True})
    settings = Settings(_env_file=None)
    client = ExternalApiClient(settings=settings, http_client=http_client)

    with pytest.raises(ExternalApiClientError, match="cotizacion"):
        client.fetch_dollar_quote()


def test_fetch_dollar_quote_wraps_http_errors() -> None:
    http_client = _mock_client(json_payload={"error": "unavailable"}, status_code=503)
    settings = Settings(_env_file=None)
    client = ExternalApiClient(settings=settings, http_client=http_client)

    with pytest.raises(ExternalApiClientError, match="cotizacion"):
        client.fetch_dollar_quote()


def _mock_client(json_payload: object, status_code: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Accept"] == "application/json"
        assert str(request.url) == "https://dolarapi.com/v1/dolares/oficial"
        return httpx.Response(status_code=status_code, json=json_payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _dollar_quote_payload() -> dict[str, object]:
    return {
        "compra": 1410,
        "venta": 1430,
        "casa": "oficial",
        "nombre": "Oficial",
        "moneda": "USD",
        "fechaActualizacion": "2026-05-31T17:59:00Z",
    }
