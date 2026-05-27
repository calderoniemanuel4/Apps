"""Cliente de Google Sheets."""

from app.core.config import Settings
from app.schemas.transaction import Transaction


class SheetsClient:
    """Cliente placeholder para lectura y escritura en Google Sheets."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def append_transactions(self, transactions: list[Transaction]) -> None:
        """Escribe movimientos validados en la planilla.

        La implementacion real debe ser idempotente o deduplicar por `external_id`.
        """
        _ = transactions
