from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class Transaction(BaseModel):
    """Core domain model representing a bank transaction."""

    id: str
    account_id: str
    date: date
    amount: Decimal  # Positive = credit, negative = debit
    currency: str
    payee: str
    notes: str = ""
    exported_at: datetime | None = None
