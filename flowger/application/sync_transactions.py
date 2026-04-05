import logging

from flowger.application.banking import BankProvider
from flowger.application.repositories import AccountRepository
from flowger.application.transaction_repository import TransactionRepository
from flowger.domain.account import Account
from flowger.domain.exceptions import BankProviderError

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

    def execute(
        self, session_id: str, accounts: list[Account] | None = None
    ) -> list[tuple[str, str]]:
        """Fetch and save transactions for accounts, returning any failures."""
        if accounts is None:
            accounts = self.__account_repository.get_accounts()
        failures: list[tuple[str, str]] = []

        for account in accounts:
            try:
                transactions = self.__provider.fetch_transactions(
                    session_id=session_id, account_id=account.id
                )
                self.__transaction_repository.save_transactions(transactions)
            except (BankProviderError, ValueError) as e:
                msg = str(e)
                logger.error("Failed to sync transactions for account %s: %s", account.id, msg)
                failures.append((account.id, msg))
                continue

        return failures
