import logging

from flowger.application.banking import BankProvider
from flowger.application.repositories import AccountRepository
from flowger.application.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)


class SyncTransactionsUseCase:
    """Use case to synchronize transactions for all stored accounts."""

    def __init__(
        self,
        provider: BankProvider,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
    ) -> None:
        self.__provider = provider
        self.__account_repository = account_repository
        self.__transaction_repository = transaction_repository

    def execute(self, session_id: str) -> None:
        """Fetch and save transactions for every account in the local database."""
        accounts = self.__account_repository.get_accounts()

        for account in accounts:
            try:
                transactions = self.__provider.fetch_transactions(
                    session_id=session_id, account_id=account.id
                )
                self.__transaction_repository.save_transactions(transactions)
            except Exception as e:
                logger.error("Failed to sync transactions for account %s: %s", account.id, e)
                continue
