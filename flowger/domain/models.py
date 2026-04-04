from datetime import date
from decimal import Decimal
from pydantic import BaseModel

class Account(BaseModel):
    """Core domain model representing a Bank Account."""
    id: str
    iban: str
    name: str
    currency: str

class Transaction(BaseModel):
    """Core domain model representing a Ledger Transaction."""
    id: str
    account_id: str
    amount: Decimal
    date: date
    description: str
