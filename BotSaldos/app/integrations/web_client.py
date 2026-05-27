"""Automatizacion web con Playwright."""

from app.core.config import Settings


class WebClient:
    """Cliente placeholder para formularios y portales sin API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_transactions(self) -> list[dict[str, object]]:
        """Obtiene datos crudos desde portales web autenticados.

        No debe loguear cookies, credenciales, HTML sensible ni estados de sesion.
        """
        return []
