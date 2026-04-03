"""Tests for the SQLite repository implementation."""

from datetime import date
from decimal import Decimal

from flowger.domain.models import Account, Transaction
from flowger.infrastructure.repositories import SQLiteTransactionRepository

_ACCOUNT = Account(
    id="acc-1",
    name="Checking",
    currency="EUR",
    provider="stub",
    iban="FR7630006000011234567890189",
)

_TX1 = Transaction(
    id="tx-2024-01-01",
    account_id="acc-1",
    date=date(2024, 1, 1),
    amount=Decimal("-42.50"),
    currency="EUR",
    description="Supermarket",
)

_TX2 = Transaction(
    id="tx-2024-01-05",
    account_id="acc-1",
    date=date(2024, 1, 5),
    amount=Decimal("2500.00"),
    currency="EUR",
    description="Salary",
)


class TestAccountStorage:
    def test_save_and_retrieve(self, repository: SQLiteTransactionRepository) -> None:
        repository.save_account(_ACCOUNT)
        result = repository.get_account("acc-1")
        assert result is not None
        assert result.id == "acc-1"
        assert result.name == "Checking"
        assert result.iban == "FR7630006000011234567890189"

    def test_get_unknown_account_returns_none(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        assert repository.get_account("unknown") is None

    def test_get_accounts_returns_all(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        acc2 = Account(id="acc-2", name="Savings", currency="EUR", provider="stub")
        repository.save_account(_ACCOUNT)
        repository.save_account(acc2)

        all_accounts = repository.get_accounts()
        ids = {a.id for a in all_accounts}
        assert ids == {"acc-1", "acc-2"}

    def test_save_account_is_idempotent(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        repository.save_account(_ACCOUNT)
        updated = Account(
            id="acc-1", name="Updated Name", currency="USD", provider="stub"
        )
        repository.save_account(updated)
        result = repository.get_account("acc-1")
        assert result is not None
        assert result.name == "Updated Name"
        assert result.currency == "USD"


class TestTransactionStorage:
    def test_upsert_returns_new_count(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        repository.save_account(_ACCOUNT)
        count = repository.upsert_transactions([_TX1, _TX2])
        assert count == 2

    def test_upsert_is_idempotent(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        repository.save_account(_ACCOUNT)
        repository.upsert_transactions([_TX1, _TX2])
        # Second call: both already exist, should insert 0
        second_count = repository.upsert_transactions([_TX1, _TX2])
        assert second_count == 0

    def test_get_transactions_ordered_by_date(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        repository.save_account(_ACCOUNT)
        # Insert in reverse order
        repository.upsert_transactions([_TX2, _TX1])
        txs = repository.get_transactions("acc-1")
        assert txs[0].date <= txs[1].date

    def test_get_last_sync_date_returns_latest(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        repository.save_account(_ACCOUNT)
        repository.upsert_transactions([_TX1, _TX2])
        last = repository.get_last_sync_date("acc-1")
        assert last == date(2024, 1, 5)

    def test_get_last_sync_date_returns_none_when_empty(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        assert repository.get_last_sync_date("acc-1") is None

    def test_amount_precision_is_preserved(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        repository.save_account(_ACCOUNT)
        repository.upsert_transactions([_TX1])
        txs = repository.get_transactions("acc-1")
        assert txs[0].amount == Decimal("-42.50")
