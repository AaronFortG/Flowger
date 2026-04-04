from typing import Protocol

from flowger.domain.account import Account


class AccountRepository(Protocol):
    """Port for local storage of Account data."""

    def save_accounts(self, accounts: list[Account]) -> None:
        """Persist a list of accounts to local storage (insert or update)."""
        ...
