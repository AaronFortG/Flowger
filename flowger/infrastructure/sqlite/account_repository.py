import sqlite3

from flowger.application.repositories import AccountRepository
from flowger.domain.account import Account


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
        rows = [(acc.id, acc.iban, acc.name, acc.currency) for acc in accounts]
        with sqlite3.connect(self.__db_path) as conn:
            conn.executemany(query, rows)

    def get_accounts(self) -> list[Account]:
        """Retrieve all stored accounts from the database."""
        query = "SELECT id, iban, name, currency FROM accounts;"
        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(query).fetchall()

        return [
            Account(id=row[0], iban=row[1], name=row[2], currency=row[3])
            for row in rows
        ]
