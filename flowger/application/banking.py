from typing import Protocol

from flowger.domain.account import Account


class BankProvider(Protocol):
    """Port for fetching data from an external banking provider."""

    def fetch_accounts(self) -> list[Account]:
        """Fetch all accounts available from the provider."""
        ...
