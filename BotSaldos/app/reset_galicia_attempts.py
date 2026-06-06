"""Reset manual de intentos fallidos de Galicia."""

from app.core.config import Settings
from app.core.login_attempt_state import LoginAttemptState
from app.core.logging_config import configure_logging


def main() -> None:
    """Resetea el contador local de intentos fallidos de Galicia."""
    settings = Settings()
    configure_logging(settings)
    LoginAttemptState(
        path=settings.galicia_attempt_state_file,
        max_attempts=settings.galicia_max_login_attempts,
    ).reset()
    print(f"Intentos de Galicia reseteados en {settings.galicia_attempt_state_file}")


if __name__ == "__main__":
    main()
