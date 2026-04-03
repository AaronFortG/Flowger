"""Domain models – plain dataclasses with no external dependencies."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal


@dataclass
class Account:
    """Represents a bank account discovered from a provider."""

    id: str
    name: str
    currency: str
    provider: str
    iban: str | None = None


@dataclass
class Transaction:
    """Represents a single bank transaction."""

    id: str
    account_id: str
    date: date
    # Stored as Decimal to avoid floating-point rounding issues.
    # Trade-off: SQLite stores this as NUMERIC (text); acceptable for an MVP.
    amount: Decimal
    currency: str
    description: str
    reference: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
