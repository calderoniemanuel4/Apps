"""Cliente de Google Sheets."""

from typing import Any

from app.core.config import Settings
from app.schemas.sheet_contract import (
    TRANSACTIONS_WORKSHEET_CONTRACT,
    WorksheetContract,
    transaction_to_sheet_row,
)
from app.schemas.transaction import Transaction


class SheetsClientError(RuntimeError):
    """Error controlado de integracion con Google Sheets."""


class SheetsClient:
    """Cliente para lectura y escritura de movimientos en Google Sheets."""

    def __init__(
        self,
        settings: Settings,
        worksheet_contract: WorksheetContract = TRANSACTIONS_WORKSHEET_CONTRACT,
        gspread_client: Any | None = None,
    ) -> None:
        self._settings = settings
        self._worksheet_contract = worksheet_contract
        self._gspread_client = gspread_client

    def append_transactions(self, transactions: list[Transaction]) -> None:
        """Escribe movimientos validados en la planilla.

        La implementacion real debe ser idempotente o deduplicar por `external_id`.
        """
        if not transactions:
            return

        worksheet = self._get_worksheet()
        self.validate_headers(worksheet.row_values(1))

        rows = [transaction_to_sheet_row(transaction) for transaction in transactions]
        worksheet.append_rows(rows, value_input_option="RAW")

    def validate_headers(self, headers: list[str]) -> None:
        """Valida encabezados antes de leer o escribir movimientos."""
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
