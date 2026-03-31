"""Esquemas de datos de la aplicacion."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GreetingMessage:
    """Representa un mensaje de saludo."""

    message: str
