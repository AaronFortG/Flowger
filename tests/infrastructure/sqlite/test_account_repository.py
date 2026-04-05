import sqlite3
from pathlib import Path

from flowger.domain.account import Account
from flowger.infrastructure.sqlite import SqliteAccountRepository, init_db


def test_sqlite_account_repository_saves_accounts(tmp_path: Path) -> None:
    """Verify that SqliteAccountRepository persists Account models to the DB."""
    # 1. Arrange
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    repo = SqliteAccountRepository(db_path)

    mock_account_1 = Account(
        id="acc_1", iban="ES11", name="Checking", currency="EUR", bank_name="Imagin", country="ES"
    )
    mock_account_2 = Account(
        id="acc_2", iban="ES22", name="Savings", currency="EUR", bank_name="Imagin", country="ES"
    )

    # 2. Act (Insert initial)
    repo.save_accounts([mock_account_1, mock_account_2])

    # 3. Assert inserts
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, iban, name, currency, bank_name, country FROM accounts ORDER BY id ASC"
        )
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert rows[0] == ("acc_1", "ES11", "Checking", "EUR", "Imagin", "ES")
        assert rows[1] == ("acc_2", "ES22", "Savings", "EUR", "Imagin", "ES")

    # 4. Act (Update existing account, simulating an upsert)
    mock_account_1_updated = Account(
        id="acc_1",
        iban="ES11",
        name="Checking Updated",
        currency="EUR",
        bank_name="Imagin",
        country="ES",
    )
    repo.save_accounts([mock_account_1_updated])

    # 5. Assert upsert worked
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts WHERE id = 'acc_1'")
        row = cursor.fetchone()
        assert row[0] == "Checking Updated"


def test_sqlite_account_repository_returns_domain_objects(tmp_path: Path) -> None:
    """Verify that get_accounts returns proper Account domain objects."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    repo = SqliteAccountRepository(db_path)
    repo.save_accounts(
        [
            Account(
                id="acc_x",
                iban="ES99",
                name="Test",
                currency="USD",
                bank_name="Imagin",
                country="ES",
            )
        ]
    )

    accounts = repo.get_accounts()

    assert len(accounts) == 1
    assert isinstance(accounts[0], Account)
    assert accounts[0].id == "acc_x"
    assert accounts[0].currency == "USD"
