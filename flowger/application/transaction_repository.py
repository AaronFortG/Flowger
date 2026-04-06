from typing import Protocol

from flowger.domain.transaction import Transaction


class TransactionRepository(Protocol):
    """Port for persisting and retrieving transactions."""

    def save_transactions(self, transactions: list[Transaction]) -> None:
        """Persist a list of transactions, upserting by id and overwriting existing rows."""
        pass

    def get_transactions_for_account(
        self, account_id: str, bank_name: str, country: str
    ) -> list[Transaction]:
        """Return all stored transactions for the given account."""
        pass

    def get_unexported_transactions(
        self, account_id: str, bank_name: str, country: str
    ) -> list[Transaction]:
        """Return all transactions for an account that have never been exported."""
        pass

    def has_transactions(self, account_id: str, bank_name: str, country: str) -> bool:
        """Return True if any transactions exist for the given account."""
        pass
