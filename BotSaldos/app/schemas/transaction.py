"""Esquemas para movimientos financieros normalizados."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class TransactionType(StrEnum):
    """Tipo de movimiento financiero."""

    INCOME = "income"
    EXPENSE = "expense"


class Transaction(BaseModel):
    """Movimiento normalizado listo para validacion y escritura."""

    occurred_on: date
    description: str = Field(min_length=1, max_length=300)
    amount: Decimal
    currency: str = Field(default="ARS", min_length=3, max_length=3)
    transaction_type: TransactionType
    source: str = Field(min_length=1, max_length=100)
    external_id: str | None = Field(default=None, max_length=200)
