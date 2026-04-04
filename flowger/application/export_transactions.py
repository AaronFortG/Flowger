from datetime import datetime, timezone

from flowger.application.export import ExportService
from flowger.application.transaction_repository import TransactionRepository


class ExportTransactionsUseCase:
    """Use case to export stored transactions to an external file format."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        export_service: ExportService,
    ) -> None:
        self.__transaction_repository = transaction_repository
        self.__export_service = export_service

    def execute(self, account_id: str, output_path: str, new_only: bool = False) -> None:
        """
        Fetch transactions for the given account and export them.
        If new_only is True, fetches unexported transactions and marks them as exported.
        """
        if new_only:
            transactions = self.__transaction_repository.get_unexported_transactions(account_id)
        else:
            transactions = self.__transaction_repository.get_transactions_for_account(account_id)


        self.__export_service.write_transactions(transactions, output_path)

        if new_only:
            now = datetime.now(tz=timezone.utc)
            for tx in transactions:
                tx.exported_at = now
            self.__transaction_repository.save_transactions(transactions)
