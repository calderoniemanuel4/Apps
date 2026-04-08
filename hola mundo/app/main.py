"""Aplicacion minima de hola mundo."""

try:
    from app.config import load_config
    from app.schemas import GreetingMessage
except ModuleNotFoundError:  # Permite ejecutar como script directo.
    from config import load_config
    from schemas import GreetingMessage

def build_message() -> GreetingMessage:
    """Construye el mensaje de saludo a partir de la configuracion."""
    config = load_config()
    return GreetingMessage(message=config.greeting)


def get_message() -> str:
    """Devuelve el texto final del saludo."""
    return build_message().message


def main() -> None:
    """Ejecuta el punto de entrada de la CLI."""
    print(get_message())


if __name__ == "__main__":
    main()
