from app.core.login_attempt_state import LoginAttemptState


def test_login_attempt_state_blocks_after_max_failures(tmp_path) -> None:
    state = LoginAttemptState(path=tmp_path / "attempts.json", max_attempts=2)

    assert state.can_attempt() is True

    state.record_failure("incorrect_password")
    assert state.snapshot().blocked is False

    state.record_failure("incorrect_password")
    assert state.snapshot().blocked is True
    assert state.can_attempt() is False


def test_login_attempt_state_reset_allows_new_attempts(tmp_path) -> None:
    state = LoginAttemptState(path=tmp_path / "attempts.json", max_attempts=1)
    state.record_failure("service_offline")

    state.reset()

    snapshot = state.snapshot()
    assert snapshot.failed_attempts == 0
    assert snapshot.blocked is False
    assert snapshot.last_failure_reason is None
