"""SQLModel ORM table definitions.

These are deliberately separate from the domain models to avoid coupling the
domain layer to SQLAlchemy/SQLModel.  The repository layer handles the
translation between these DB models and the domain dataclasses.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class AccountTable(SQLModel, table=True):
    __tablename__ = "accounts"

    id: str = Field(primary_key=True)
    name: str
    currency: str
    provider: str
    iban: str | None = Field(default=None)


class TransactionTable(SQLModel, table=True):
    __tablename__ = "transactions"

    id: str = Field(primary_key=True)
    account_id: str = Field(foreign_key="accounts.id")
    date: date
    # Stored as NUMERIC in SQLite (text-based, preserves decimal precision).
    amount: Decimal
    currency: str
    description: str
    reference: str | None = Field(default=None)
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC)
    )
