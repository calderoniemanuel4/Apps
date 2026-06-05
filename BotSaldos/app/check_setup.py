"""Chequeos locales de configuracion antes de escribir en Google Sheets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.integrations.api_client import ExternalApiClient
from app.integrations.sheets_client import SheetsClient
from app.integrations.web_client import WebClient


class QuoteSource(Protocol):
    """Contrato minimo para validar la API externa."""

    def fetch_dollar_quote(self) -> dict[str, object]:
        """Obtiene una cotizacion cruda."""


class WorksheetValidator(Protocol):
    """Contrato minimo para validar Google Sheets sin escribir."""

    def validate_configured_worksheet(self) -> list[str]:
        """Valida acceso y encabezados de la worksheet configurada."""


@dataclass(frozen=True)
class SetupCheck:
    """Resultado de un chequeo de setup."""

    name: str
    ok: bool
    message: str


def run_setup_checks(
    settings: Settings,
    api_client: QuoteSource | None = None,
    sheets_client: WorksheetValidator | None = None,
) -> list[SetupCheck]:
    """Ejecuta chequeos operativos sin escribir datos."""
    checks: list[SetupCheck] = []
    checks.append(_check_credentials_path(settings.google_application_credentials))
    checks.append(_check_spreadsheet_id(settings.google_sheets_spreadsheet_id))
    checks.append(_check_api(api_client or ExternalApiClient(settings)))
    checks.append(_check_playwright_storage_state(WebClient(settings)))

    if settings.google_application_credentials and settings.google_sheets_spreadsheet_id:
        checks.append(_check_google_sheets(sheets_client or SheetsClient(settings)))
    else:
        checks.append(
            SetupCheck(
                name="google_sheets_access",
                ok=False,
                message="No se valido Sheets porque faltan credenciales o spreadsheet id.",
            )
        )

    return checks


def main() -> None:
    """Entrypoint CLI para validar setup local."""
    settings = Settings()
    configure_logging(settings)
    checks = run_setup_checks(settings)

    for check in checks:
        status = "OK" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.message}")

    if not all(check.ok for check in checks):
        raise SystemExit(1)


def _check_credentials_path(path: Path | None) -> SetupCheck:
    if path is None:
        return SetupCheck(
            name="google_credentials",
            ok=False,
            message="GOOGLE_APPLICATION_CREDENTIALS no esta configurado.",
        )
    if not path.exists():
        return SetupCheck(
            name="google_credentials",
            ok=False,
            message="GOOGLE_APPLICATION_CREDENTIALS apunta a un archivo inexistente.",
        )
    return SetupCheck(
        name="google_credentials",
        ok=True,
        message="Archivo de credenciales encontrado.",
    )


def _check_spreadsheet_id(spreadsheet_id: str | None) -> SetupCheck:
    if not spreadsheet_id:
        return SetupCheck(
            name="google_spreadsheet_id",
            ok=False,
            message="GOOGLE_SHEETS_SPREADSHEET_ID no esta configurado.",
        )
    return SetupCheck(
        name="google_spreadsheet_id",
        ok=True,
        message="Spreadsheet id configurado.",
    )


def _check_api(api_client: QuoteSource) -> SetupCheck:
    try:
        quote = api_client.fetch_dollar_quote()
    except Exception as exc:
        return SetupCheck(
            name="external_api",
            ok=False,
            message=f"No se pudo obtener cotizacion: {exc}",
        )

    quote_name = quote.get("nombre") or quote.get("casa") or "cotizacion sin nombre"
    return SetupCheck(
        name="external_api",
        ok=True,
        message=f"API respondio correctamente: {quote_name}.",
    )


def _check_google_sheets(sheets_client: WorksheetValidator) -> SetupCheck:
    try:
        headers = sheets_client.validate_configured_worksheet()
    except Exception as exc:
        return SetupCheck(
            name="google_sheets_access",
            ok=False,
            message=f"No se pudo validar la worksheet: {exc}",
        )

    return SetupCheck(
        name="google_sheets_access",
        ok=True,
        message=f"Worksheet accesible con {len(headers)} encabezados validos.",
    )


def _check_playwright_storage_state(web_client: WebClient) -> SetupCheck:
    if web_client.has_storage_state():
        return SetupCheck(
            name="playwright_storage_state",
            ok=True,
            message="Storage state de Playwright encontrado.",
        )

    return SetupCheck(
        name="playwright_storage_state",
        ok=True,
        message="Storage state no configurado aun; requerido solo para portales autenticados.",
    )


if __name__ == "__main__":
    main()
