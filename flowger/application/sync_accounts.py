from flowger.application.banking import BankProvider
from flowger.application.repositories import AccountRepository


class SyncAccountsUseCase:
    """Use case to synchronize accounts from the provider to local storage."""

    def __init__(self, provider: BankProvider, repository: AccountRepository) -> None:
        self.__provider = provider
        self.__repository = repository

    def execute(self, session_id: str) -> None:
        """Fetch accounts from the provider for the given session and save them locally."""
        accounts = self.__provider.fetch_accounts(session_id=session_id)
        self.__repository.save_accounts(accounts)
