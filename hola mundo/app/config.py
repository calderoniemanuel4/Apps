"""Configuracion de la aplicacion."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    """Configuracion minima para la aplicacion."""

    greeting: str


def load_config() -> AppConfig:
    """Carga configuracion desde variables de entorno con defaults seguros."""
    greeting = os.getenv("APP_GREETING", "Hola mundo").strip()
    if not greeting:
        greeting = "Hola mundo"
    return AppConfig(greeting=greeting)
