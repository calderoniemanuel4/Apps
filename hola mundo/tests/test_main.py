from app.main import build_message, get_message


def test_get_message() -> None:
    assert get_message() == "Hola mundo"


def test_build_message_returns_typed_schema() -> None:
    message = build_message()
    assert message.message == "Hola mundo"
