import sqlite3
from pathlib import Path

from flowger.domain.account import Account
from flowger.infrastructure.database import SqliteAccountRepository, init_db


def test_sqlite_account_repository_saves_accounts(tmp_path: Path) -> None:
    """Verify that SqliteAccountRepository persists Account models to the DB."""
    # 1. Arrange
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    repo = SqliteAccountRepository(db_path)
    
    mock_account_1 = Account(id="acc_1", iban="ES11", name="Checking", currency="EUR")
    mock_account_2 = Account(id="acc_2", iban="ES22", name="Savings", currency="EUR")
    
    # 2. Act (Insert initial)
    repo.save_accounts([mock_account_1, mock_account_2])
    
    # 3. Assert inserts
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, iban, name, currency FROM accounts ORDER BY id ASC")
        rows = cursor.fetchall()
        
        assert len(rows) == 2
        assert rows[0] == ("acc_1", "ES11", "Checking", "EUR")
        assert rows[1] == ("acc_2", "ES22", "Savings", "EUR")
        
    # 4. Act (Update existing account, simulating an upsert)
    mock_account_1_updated = Account(
        id="acc_1", iban="ES11", name="Checking Updated", currency="EUR"
    )
    repo.save_accounts([mock_account_1_updated])
    
    # 5. Assert upsert worked
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts WHERE id = 'acc_1'")
        row = cursor.fetchone()
        assert row[0] == "Checking Updated"
