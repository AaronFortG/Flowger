"""Ports (interfaces) for external dependencies.

These abstractions exist because real substitution is likely:
- BankingProvider: Enable Banking today, another provider tomorrow.
- TransactionRepository: SQLite today, PostgreSQL potentially later.
"""

from abc import ABC, abstractmethod
from datetime import date

from flowger.domain.models import Account, Transaction


class BankingProvider(ABC):
    """Provides access to bank accounts and transactions from an external API."""

    @abstractmethod
    def get_accounts(self) -> list[Account]:
        """Return all accounts accessible with the configured credentials."""
        ...

    @abstractmethod
    def get_transactions(
        self, account_id: str, from_date: date, to_date: date
    ) -> list[Transaction]:
        """Return transactions for an account within a date range (inclusive)."""
        ...


class TransactionRepository(ABC):
    """Persists accounts and transactions locally."""

    @abstractmethod
    def save_account(self, account: Account) -> None:
        """Insert or update an account record."""
        ...

    @abstractmethod
    def get_accounts(self) -> list[Account]:
        """Return all stored accounts."""
        ...

    @abstractmethod
    def get_account(self, account_id: str) -> Account | None:
        """Return a single account by ID, or None if not found."""
        ...

    @abstractmethod
    def upsert_transactions(self, transactions: list[Transaction]) -> int:
        """Persist new transactions, ignoring already-stored ones.

        Returns the number of newly inserted transactions.
        """
        ...

    @abstractmethod
    def get_transactions(self, account_id: str) -> list[Transaction]:
        """Return all transactions for an account, ordered by date ascending."""
        ...

    @abstractmethod
    def get_last_sync_date(self, account_id: str) -> date | None:
        """Return the date of the most recent stored transaction, or None."""
        ...
