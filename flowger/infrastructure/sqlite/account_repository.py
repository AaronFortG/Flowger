import sqlite3

from flowger.application.repositories import AccountRepository
from flowger.domain.account import Account


class SqliteAccountRepository(AccountRepository):
    """Concrete repository implementing Account persistence using SQLite."""

    _TABLE_NAME = "accounts"
    _QUERY_SAVE = f"""
        INSERT INTO {_TABLE_NAME} (id, iban, name, currency)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            iban=excluded.iban,
            name=excluded.name,
            currency=excluded.currency;
    """
    _QUERY_GET_ALL = f"SELECT id, iban, name, currency FROM {_TABLE_NAME};"

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_accounts(self, accounts: list[Account]) -> None:
        """Insert or replace accounts in the database."""
        rows = [(acc.id, acc.iban, acc.name, acc.currency) for acc in accounts]
        with sqlite3.connect(self.__db_path) as conn:
            conn.executemany(self._QUERY_SAVE, rows)

    def get_accounts(self) -> list[Account]:
        """Retrieve all stored accounts from the database."""
        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(self._QUERY_GET_ALL).fetchall()

        return [
            Account(id=row[0], iban=row[1], name=row[2], currency=row[3])
            for row in rows
        ]
