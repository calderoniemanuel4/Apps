"""Esquemas simples para saldos monetarios."""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class BalanceStatus(StrEnum):
    """Estado de consulta de saldo web."""

    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    BLOCKED = "blocked"


class MonetaryBalance(BaseModel):
    """Saldo monetario normalizado desde un portal web."""

    amount: Decimal | None = None
    currency: str = Field(default="ARS", min_length=3, max_length=3)
    source: str = Field(default="santander", min_length=1, max_length=100)
    status: BalanceStatus
    failure_reason: str | None = Field(default=None, max_length=200)
