from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from flowger.application.export_transactions import ExportTransactionsUseCase
from flowger.domain.transaction import Transaction


def _make_transaction(
    tx_id: str = "tx1",
    account_id: str = "acc1",
    bank_name: str = "bank1",
    country: str = "FI",
) -> Transaction:
    return Transaction(
        id=tx_id,
        account_id=account_id,
        bank_name=bank_name,
        country=country,
        date=date(2026, 4, 1),
        amount=Decimal("-50.00"),
        currency="EUR",
        payee="Test",
    )


def test_export_transactions_calls_service() -> None:
    """Verify the use case reads from the repo and passes results to the export service."""
    tx = _make_transaction()
    transaction_repo = Mock()
    transaction_repo.get_transactions_for_account.return_value = [tx]
    export_service = Mock()

    use_case = ExportTransactionsUseCase(
        transaction_repository=transaction_repo,
        export_service=export_service,
    )
    use_case.execute(account_id="acc1", bank_name="bank1", country="FI", output_path="out.csv")

    transaction_repo.get_transactions_for_account.assert_called_once_with("acc1", "bank1", "FI")
    export_service.write_transactions.assert_called_once_with([tx], "out.csv")


def test_export_transactions_empty_account() -> None:
    """Verify the use case passes an empty list to the exporter when there are no transactions."""
    transaction_repo = Mock()
    transaction_repo.get_transactions_for_account.return_value = []
    export_service = Mock()

    use_case = ExportTransactionsUseCase(
        transaction_repository=transaction_repo,
        export_service=export_service,
    )
    use_case.execute(account_id="acc1", bank_name="bank1", country="FI", output_path="out.csv")

    export_service.write_transactions.assert_called_once_with([], "out.csv")


def test_export_transactions_new_only_marks_as_exported() -> None:
    """Verify that new_only=True marks transactions as exported with the current time."""
    tx = _make_transaction()
    transaction_repo = Mock()
    transaction_repo.get_unexported_transactions.return_value = [tx]
    export_service = Mock()

    use_case = ExportTransactionsUseCase(
        transaction_repository=transaction_repo,
        export_service=export_service,
    )
    use_case.execute(
        account_id="acc1", bank_name="bank1", country="FI", output_path="out.csv", new_only=True
    )

    transaction_repo.get_unexported_transactions.assert_called_once_with("acc1", "bank1", "FI")
    export_service.write_transactions.assert_called_once_with([tx], "out.csv")
    transaction_repo.save_transactions.assert_called_once()
    saved_txs = transaction_repo.save_transactions.call_args[0][0]
    assert len(saved_txs) == 1
    assert saved_txs[0].exported_at is not None
