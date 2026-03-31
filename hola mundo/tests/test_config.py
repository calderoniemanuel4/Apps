from app.config import load_config


def test_load_config_uses_default_greeting(monkeypatch) -> None:
    monkeypatch.delenv("APP_GREETING", raising=False)
    config = load_config()
    assert config.greeting == "Hola mundo"


def test_load_config_reads_env_greeting(monkeypatch) -> None:
    monkeypatch.setenv("APP_GREETING", "Hola equipo")
    config = load_config()
    assert config.greeting == "Hola equipo"


def test_load_config_handles_empty_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_GREETING", "   ")
    config = load_config()
    assert config.greeting == "Hola mundo"
