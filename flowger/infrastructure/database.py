import sqlite3

from flowger.application.repositories import AccountRepository
from flowger.domain.account import Account


def init_db(db_path: str) -> None:
    """Initialize the SQLite database schema."""
    query = """
    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        iban TEXT NOT NULL,
        name TEXT NOT NULL,
        currency TEXT NOT NULL
    );
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(query)


class SqliteAccountRepository(AccountRepository):
    """Concrete repository implementing Account persistence using SQLite."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_accounts(self, accounts: list[Account]) -> None:
        """Insert or replace accounts in the database."""
        query = """
        INSERT INTO accounts (id, iban, name, currency)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            iban=excluded.iban,
            name=excluded.name,
            currency=excluded.currency;
        """
        
        # Convert domain objects into tuples for sqlite execution
        rows = [
            (acc.id, acc.iban, acc.name, acc.currency)
            for acc in accounts
        ]

        with sqlite3.connect(self.__db_path) as conn:
            conn.executemany(query, rows)
