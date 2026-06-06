"""Cliente de Google Sheets."""

import logging
from typing import Any

from app.core.config import Settings
from app.schemas.sheet_contract import (
    USD_QUOTE_WORKSHEET_CONTRACT,
    WorksheetContract,
    dollar_quote_to_sheet_row,
)
from app.schemas.transaction import MonetaryBalance

logger = logging.getLogger(__name__)


class SheetsClientError(RuntimeError):
    """Error controlado de integracion con Google Sheets."""


class SheetsClient:
    """Cliente para escritura de cotizaciones en Google Sheets."""

    def __init__(
        self,
        settings: Settings,
        worksheet_contract: WorksheetContract = USD_QUOTE_WORKSHEET_CONTRACT,
        gspread_client: Any | None = None,
    ) -> None:
        self._settings = settings
        self._worksheet_contract = worksheet_contract
        self._gspread_client = gspread_client

    def append_dollar_quote(
        self,
        quote: dict[str, object],
        santander_balance: MonetaryBalance | None = None,
        balances: dict[str, MonetaryBalance] | None = None,
    ) -> int:
        """Escribe la respuesta de cotizacion en la planilla."""
        try:
            worksheet = self._get_worksheet()
            headers = worksheet.row_values(1)
            self.validate_headers(headers)

            row = dollar_quote_to_sheet_row(
                quote=quote,
                santander_balance=santander_balance,
                balances=balances,
            )
            worksheet.append_rows([row], value_input_option="RAW")
            logger.info("dollar_quote_appended_to_sheet")
            return 1
        except Exception as exc:
            if self._is_gspread_exception(exc):
                raise SheetsClientError("No se pudo leer o escribir en Google Sheets") from exc
            raise

    def validate_configured_worksheet(self) -> list[str]:
        """Valida acceso y encabezados de la worksheet configurada sin escribir."""
        try:
            worksheet = self._get_worksheet()
            headers = worksheet.row_values(1)
            self.validate_headers(headers)
            logger.info("google_sheets_worksheet_validated")
            return headers
        except Exception as exc:
            if self._is_gspread_exception(exc):
                raise SheetsClientError("No se pudo validar Google Sheets") from exc
            raise

    def update_configured_headers(self) -> list[str]:
        """Actualiza la primera fila con los encabezados esperados."""
        try:
            worksheet = self._get_worksheet()
            headers = list(self._worksheet_contract.required_headers)
            worksheet.update([headers], "A1", value_input_option="RAW")
            logger.info("google_sheets_headers_updated")
            return headers
        except Exception as exc:
            if self._is_gspread_exception(exc):
                raise SheetsClientError("No se pudieron actualizar headers en Google Sheets") from exc
            raise

    def validate_headers(self, headers: list[str]) -> None:
        """Valida encabezados antes de escribir cotizaciones."""
        self._worksheet_contract.validate_headers(headers)

    def _get_worksheet(self) -> Any:
        """Obtiene la worksheet configurada desde Google Sheets."""
        if not self._settings.google_sheets_spreadsheet_id:
            raise SheetsClientError("GOOGLE_SHEETS_SPREADSHEET_ID no esta configurado")

        client = self._gspread_client or self._build_gspread_client()
        try:
            spreadsheet = client.open_by_key(self._settings.google_sheets_spreadsheet_id)
            return spreadsheet.worksheet(self._settings.google_sheets_worksheet_name)
        except Exception as exc:
            if self._is_gspread_exception(exc):
                raise SheetsClientError(
                    "No se pudo abrir la planilla o worksheet configurada"
                ) from exc
            raise

    def _build_gspread_client(self) -> Any:
        """Construye el cliente gspread usando cuenta de servicio."""
        if self._settings.google_application_credentials is None:
            raise SheetsClientError("GOOGLE_APPLICATION_CREDENTIALS no esta configurado")

        try:
            import gspread
        except ImportError as exc:
            raise SheetsClientError(
                "gspread no esta instalado. Instala el extra de automatizacion con "
                '`pip install -e ".[automation]"`.'
            ) from exc

        return gspread.service_account(
            filename=str(self._settings.google_application_credentials),
        )

    @staticmethod
    def _is_gspread_exception(exc: Exception) -> bool:
        """Detecta excepciones de gspread sin requerir la dependencia en tests base."""
        return exc.__class__.__module__.startswith("gspread")
