from typing import Protocol

from flowger.domain.transaction import Transaction


class TransactionRepository(Protocol):
    """Port for persisting and retrieving transactions."""

    def save_transactions(self, transactions: list[Transaction]) -> None:
        """Persist a list of transactions. Ignores duplicates by id."""
        pass

    def get_transactions_for_account(self, account_id: str) -> list[Transaction]:
        """Return all stored transactions for the given account."""
        pass
