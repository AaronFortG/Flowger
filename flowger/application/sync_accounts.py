from flowger.application.banking import BankProvider
from flowger.application.repositories import AccountRepository


class SyncAccountsUseCase:
    """Use case to synchronize accounts from the provider to local storage."""

    def __init__(self, provider: BankProvider, repository: AccountRepository) -> None:
        self.provider = provider
        self.repository = repository

    def execute(self) -> None:
        """Fetch accounts from the provider and save them locally."""
        accounts = self.provider.fetch_accounts()
        self.repository.save_accounts(accounts)
