from typing import Protocol

from flowger.domain.account import Account
from flowger.domain.transaction import Transaction


class BankProvider(Protocol):
    """Port for fetching data from an external banking provider."""

    def fetch_accounts(self, session_id: str) -> list[Account]:
        """Fetch all accounts available for the given authorized session."""
        pass

    def fetch_transactions(self, session_id: str, account_id: str) -> list[Transaction]:
        """Fetch transactions for a specific account under an authorized session."""
        pass
