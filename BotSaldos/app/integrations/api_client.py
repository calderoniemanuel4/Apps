"""Cliente para APIs externas gratuitas."""

from app.core.config import Settings


class ExternalApiClient:
    """Cliente placeholder para consultas HTTP externas."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_transactions(self) -> list[dict[str, object]]:
        """Obtiene datos crudos desde APIs externas.

        La implementacion real debe definir timeouts, errores explicitos y sanitizacion de logs.
        """
        return []
