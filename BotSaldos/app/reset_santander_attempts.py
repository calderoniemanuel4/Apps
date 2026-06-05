"""Reset manual de intentos fallidos de Santander."""

from app.core.config import Settings
from app.core.login_attempt_state import LoginAttemptState
from app.core.logging_config import configure_logging


def main() -> None:
    """Resetea el contador local de intentos fallidos de Santander."""
    settings = Settings()
    configure_logging(settings)
    LoginAttemptState(
        path=settings.santander_attempt_state_file,
        max_attempts=settings.santander_max_login_attempts,
    ).reset()
    print(f"Intentos de Santander reseteados en {settings.santander_attempt_state_file}")


if __name__ == "__main__":
    main()
