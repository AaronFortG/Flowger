from flowger.application.banking import BankProvider
from flowger.application.repositories import AccountRepository


class SyncAccountsUseCase:
    """Use case to synchronize accounts from the provider to local storage."""

    def __init__(self, provider: BankProvider, repository: AccountRepository) -> None:
        self.__provider = provider
        self.__repository = repository

    def execute(self) -> None:
        """Fetch accounts from the provider and save them locally."""
        accounts = self.__provider.fetch_accounts()
        self.__repository.save_accounts(accounts)
