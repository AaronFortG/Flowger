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

    def execute(self, account_id: str, output_path: str) -> None:
        """Fetch transactions for the given account and export them."""
        transactions = self.__transaction_repository.get_transactions_for_account(account_id)
        self.__export_service.write_transactions(transactions, output_path)
