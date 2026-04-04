from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from flowger.application.sync_transactions import SyncTransactionsUseCase
from flowger.domain.account import Account
from flowger.domain.exceptions import BankProviderError
from flowger.domain.transaction import Transaction


def test_sync_transactions_use_case() -> None:
    # 1. Arrange
    provider = Mock()
    account_repo = Mock()
    transaction_repo = Mock()

    account = Account(id="acc_1", iban="IBAN1", name="Acc 1", currency="EUR")
    account_repo.get_accounts.return_value = [account]

    transaction = Transaction(
        id="tx_1",
        account_id="acc_1",
        date=date(2026, 4, 4),
        amount=Decimal("100.00"),
        currency="EUR",
        payee="Test TX",
    )
    provider.fetch_transactions.return_value = [transaction]

    use_case = SyncTransactionsUseCase(
        provider=provider,
        account_repository=account_repo,
        transaction_repository=transaction_repo,
    )

    # 2. Act
    use_case.execute(session_id="sess_123")

    # 3. Assert
    provider.fetch_transactions.assert_called_once_with(session_id="sess_123", account_id="acc_1")
    transaction_repo.save_transactions.assert_called_once_with([transaction])


def test_sync_transactions_continues_on_failure() -> None:
    """Verify that a failure in one account doesn't stop the whole sync."""
    # 1. Arrange
    provider = Mock()
    account_repo = Mock()
    transaction_repo = Mock()

    acc1 = Account(id="fail", iban="IBAN1", name="Fail", currency="EUR")
    acc2 = Account(id="success", iban="IBAN2", name="Success", currency="EUR")
    account_repo.get_accounts.return_value = [acc1, acc2]

    # First call raises BankProviderError, second succeeds
    provider.fetch_transactions.side_effect = [BankProviderError("API Error"), []]

    use_case = SyncTransactionsUseCase(
        provider=provider,
        account_repository=account_repo,
        transaction_repository=transaction_repo,
    )

    # 2. Act
    use_case.execute(session_id="sess_123")

    # 3. Assert
    assert provider.fetch_transactions.call_count == 2
    # Verify save was called for the successful one (acc2)
    transaction_repo.save_transactions.assert_called_once_with([])
