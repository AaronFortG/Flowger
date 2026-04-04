from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class Transaction(BaseModel):
    """Core domain model representing a Ledger Transaction."""

    id: str
    account_id: str
    amount: Decimal
    date: date
    description: str
