"""Application ports (interfaces) defining external dependencies."""

from typing import Protocol

from flowger.domain.models import Account


class BankProvider(Protocol):
    """Port for fetching data from an external banking provider."""

    def fetch_accounts(self) -> list[Account]:
        """Fetch all accounts available from the provider."""
        ...


class AccountRepository(Protocol):
    """Port for local storage of Account data."""

    def save_accounts(self, accounts: list[Account]) -> None:
        """Persist a list of accounts to local storage (insert or update)."""
        ...
