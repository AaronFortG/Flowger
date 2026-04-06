from typing import Protocol

from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.domain.transaction import Transaction


class BankProvider(Protocol):
    """Port for fetching data from an external banking provider."""

    def authorize_session(
        self, code: str, bank_name: str, country: str
    ) -> tuple[BankSession, list[Account]]:
        """Exchange redirect code for session and full list of available accounts."""
        pass

    def fetch_transactions(
        self, session_id: str, account_id: str, bank_name: str, country: str
    ) -> list[Transaction]:
        """Fetch transactions for a specific account under an authorized session."""
        pass
