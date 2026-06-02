"""Cliente para APIs externas gratuitas."""

import logging
from numbers import Number
from typing import Any

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class ExternalApiClientError(RuntimeError):
    """Error controlado al consultar APIs externas."""


class ExternalApiClient:
    """Cliente HTTP para obtener la cotizacion del dolar desde DolarApi."""

    def __init__(self, settings: Settings, http_client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._http_client = http_client

    def fetch_dollar_quote(self) -> dict[str, object]:
        """Obtiene la respuesta cruda de cotizacion y valida que tenga un valor usable."""
        client = self._http_client or httpx.Client(
            timeout=self._settings.external_api_timeout_seconds,
        )
        close_client = self._http_client is None

        try:
            response = client.get(
                self._settings.external_api_dollar_quote_url,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            quote = self._extract_quote(response.json())
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise ExternalApiClientError(
                "No se pudo obtener la cotizacion del dolar desde la API externa"
            ) from exc
        finally:
            if close_client:
                client.close()

        logger.info(
            "external_api_dollar_quote_fetched",
            extra={
                "casa": quote.get("casa"),
                "nombre": quote.get("nombre"),
            },
        )
        return quote

    def _extract_quote(self, payload: Any) -> dict[str, object]:
        """Extrae la respuesta cruda cuando contiene al menos una cotizacion numerica."""
        if not isinstance(payload, dict):
            raise ValueError("La respuesta debe ser un objeto JSON")

        quote_value = payload.get("venta", payload.get("compra"))
        if isinstance(quote_value, bool) or not isinstance(quote_value, Number):
            raise ValueError("La respuesta debe contener una cotizacion numerica")

        return payload
