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


def test_sqlite_account_repository_composite_primary_key(tmp_path: Path) -> None:
    """Verify that same account ID can exist for different banks (composite PK)."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    repo = SqliteAccountRepository(db_path)

    # 1. Save same account ID for two different banks
    acc_bank_a = Account(
        id="shared_id",
        iban="ES11",
        name="Bank A Account",
        currency="EUR",
        bank_name="BankA",
        country="ES",
    )
    acc_bank_b = Account(
        id="shared_id",
        iban="ES22",
        name="Bank B Account",
        currency="EUR",
        bank_name="BankB",
        country="ES",
    )

    repo.save_accounts([acc_bank_a, acc_bank_b])

    # 2. Verify both exist and are distinct
    accounts = repo.get_accounts()
    assert len(accounts) == 2

    # 3. Verify filtering works correctly
    bank_a_accounts = repo.get_accounts(bank_name="BankA", country="ES")
    assert len(bank_a_accounts) == 1
    assert bank_a_accounts[0].name == "Bank A Account"

    bank_b_accounts = repo.get_accounts(bank_name="BankB", country="ES")
    assert len(bank_b_accounts) == 1
    assert bank_b_accounts[0].name == "Bank B Account"
