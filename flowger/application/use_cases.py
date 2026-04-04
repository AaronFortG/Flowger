"""Application use cases containing business orchestration logic."""

from flowger.application.ports import AccountRepository, BankProvider


class SyncAccountsUseCase:
    """Use case to synchronize accounts from the provider to local storage."""

    def __init__(self, provider: BankProvider, repository: AccountRepository):
        self.provider = provider
        self.repository = repository

    def execute(self) -> None:
        """Fetch accounts from the provider and save them locally."""
        accounts = self.provider.fetch_accounts()
        self.repository.save_accounts(accounts)
