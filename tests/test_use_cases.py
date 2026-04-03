"""Tests for application use cases.

These tests exercise the sync and export use cases end-to-end using:
- StubBankingProvider (deterministic fake data)
- SQLiteTransactionRepository with an in-memory SQLite database
"""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from flowger.application.use_cases import (
    export_account_transactions,
    sync_account_transactions,
)
from flowger.domain.models import Account
from flowger.infrastructure.repositories import SQLiteTransactionRepository
from flowger.infrastructure.stub_provider import StubBankingProvider

_ACCOUNT = Account(
    id="acc-stub-001",
    name="Main Checking (stub)",
    currency="EUR",
    provider="stub",
    iban="FR7630006000011234567890189",
)


@pytest.fixture()
def provider() -> StubBankingProvider:
    return StubBankingProvider()


class TestSyncAccountTransactions:
    def test_initial_sync_inserts_transactions(
        self, repository: SQLiteTransactionRepository, provider: StubBankingProvider
    ) -> None:
        repository.save_account(_ACCOUNT)
        count = sync_account_transactions(
            account_id=_ACCOUNT.id,
            provider=provider,
            repository=repository,
            days_back=7,
        )
        # 7 days back + today = 8 transactions
        assert count == 8

    def test_second_sync_does_not_duplicate(
        self, repository: SQLiteTransactionRepository, provider: StubBankingProvider
    ) -> None:
        repository.save_account(_ACCOUNT)
        sync_account_transactions(
            account_id=_ACCOUNT.id,
            provider=provider,
            repository=repository,
            days_back=7,
        )
        second_count = sync_account_transactions(
            account_id=_ACCOUNT.id,
            provider=provider,
            repository=repository,
            days_back=7,
        )
        # The second sync requests transactions after the last stored date.
        # Only today (1 transaction) would be new *if* today wasn't already stored.
        # Since all days up to today were stored, second_count == 0.
        assert second_count == 0

    def test_incremental_sync_only_fetches_new(
        self, repository: SQLiteTransactionRepository
    ) -> None:
        """Manually seed a past transaction; next sync should start from day+1."""
        from flowger.domain.models import Transaction

        repository.save_account(_ACCOUNT)
        yesterday = date.today() - timedelta(days=1)
        old_tx = Transaction(
            id=f"tx-{_ACCOUNT.id}-{yesterday.isoformat()}",
            account_id=_ACCOUNT.id,
            date=yesterday,
            amount=Decimal("-42.50"),
            currency="EUR",
            description="Old transaction",
        )
        repository.upsert_transactions([old_tx])

        # Sync should now only request from today onward.
        provider = StubBankingProvider()
        count = sync_account_transactions(
            account_id=_ACCOUNT.id,
            provider=provider,
            repository=repository,
            days_back=30,
        )
        # Today's transaction is new; yesterday's is already stored.
        assert count == 1


class TestExportAccountTransactions:
    def test_export_creates_csv_file(
        self,
        repository: SQLiteTransactionRepository,
        provider: StubBankingProvider,
        tmp_path: Path,
    ) -> None:
        repository.save_account(_ACCOUNT)
        sync_account_transactions(
            account_id=_ACCOUNT.id,
            provider=provider,
            repository=repository,
            days_back=5,
        )

        filepath = export_account_transactions(_ACCOUNT, repository, tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".csv"
        assert filepath.name == f"{_ACCOUNT.id}.csv"

    def test_export_content_matches_stored_transactions(
        self,
        repository: SQLiteTransactionRepository,
        provider: StubBankingProvider,
        tmp_path: Path,
    ) -> None:
        repository.save_account(_ACCOUNT)
        sync_account_transactions(
            account_id=_ACCOUNT.id,
            provider=provider,
            repository=repository,
            days_back=3,
        )

        filepath = export_account_transactions(_ACCOUNT, repository, tmp_path)
        content = filepath.read_text(encoding="utf-8")

        assert "Date,Payee,Notes,Amount" in content
        # 3 days back + today = 4 rows + 1 header
        lines = [line for line in content.splitlines() if line.strip()]
        assert len(lines) == 5  # 1 header + 4 data rows

    def test_export_empty_account_creates_header_only(
        self, repository: SQLiteTransactionRepository, tmp_path: Path
    ) -> None:
        repository.save_account(_ACCOUNT)

        filepath = export_account_transactions(_ACCOUNT, repository, tmp_path)
        content = filepath.read_text(encoding="utf-8")

        assert "Date,Payee,Notes,Amount" in content
        lines = [line for line in content.splitlines() if line.strip()]
        assert len(lines) == 1  # header only
