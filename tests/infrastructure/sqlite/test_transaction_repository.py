import datetime
from decimal import Decimal
from pathlib import Path

from flowger.domain.transaction import Transaction
from flowger.infrastructure.sqlite import SqliteTransactionRepository, init_db


def test_sqlite_transaction_repository_upserts_and_fetches(tmp_path: Path) -> None:
    """Verify that SqliteTransactionRepository persists and upserts transactions."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    repo = SqliteTransactionRepository(db_path)

    tx1 = Transaction(
        id="t1",
        account_id="acc1",
        date=datetime.date(2023, 1, 1),
        amount=Decimal("10.50"),
        currency="EUR",
        payee="Shop",
        notes="Groceries",
    )

    # 1. Insert
    repo.save_transactions([tx1])

    fetched = repo.get_transactions_for_account("acc1")
    assert len(fetched) == 1
    assert fetched[0].id == "t1"
    assert fetched[0].amount == Decimal("10.50")
    assert fetched[0].exported_at is None

    # 2. Fetch unexported (should find it)
    unexported = repo.get_unexported_transactions("acc1")
    assert len(unexported) == 1
    assert unexported[0].id == "t1"

    # 3. Upsert (update amount and set exported_at)
    export_time = datetime.datetime(2023, 1, 2, 12, 0, 0, tzinfo=datetime.timezone.utc)
    tx1.amount = Decimal("20.00")
    tx1.exported_at = export_time
    repo.save_transactions([tx1])

    # 4. Verify unexported is empty now
    unexported_after = repo.get_unexported_transactions("acc1")
    assert len(unexported_after) == 0

    # 5. Verify updates persisted correctly
    fetched_after = repo.get_transactions_for_account("acc1")
    assert len(fetched_after) == 1
    assert fetched_after[0].amount == Decimal("20.00")
    assert fetched_after[0].exported_at == export_time
