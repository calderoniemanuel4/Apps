from decimal import Decimal
from pathlib import Path

from app.core.balance_state import BalanceState
from app.schemas.transaction import BalanceStatus, MonetaryBalance


def test_balance_state_saves_and_reads_successful_balance(tmp_path: Path) -> None:
    state = BalanceState(tmp_path / "balances.json")

    state.save(
        MonetaryBalance(
            amount=Decimal("1234.56"),
            currency="ARS",
            source="santander",
            status=BalanceStatus.SUCCESS,
        )
    )

    snapshot = state.get("santander")

    assert snapshot is not None
    assert snapshot.amount == Decimal("1234.56")
    assert snapshot.currency == "ARS"
    assert snapshot.source == "santander"
    assert snapshot.last_updated_at is not None


def test_balance_state_ignores_missing_amount(tmp_path: Path) -> None:
    state = BalanceState(tmp_path / "balances.json")

    state.save(MonetaryBalance(status=BalanceStatus.SUCCESS, source="galicia"))

    assert state.get("galicia") is None
