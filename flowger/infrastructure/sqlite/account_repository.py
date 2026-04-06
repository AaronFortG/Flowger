import sqlite3

from flowger.domain.account import Account

_QUERY_SAVE = """
    INSERT INTO accounts (id, iban, name, currency, bank_name, country)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(bank_name, country, id) DO UPDATE SET
        iban=excluded.iban,
        name=excluded.name,
        currency=excluded.currency,
        bank_name=excluded.bank_name,
        country=excluded.country;
"""

_QUERY_GET_ALL = "SELECT id, iban, name, currency, bank_name, country FROM accounts;"
_QUERY_GET_FILTERED = """
    SELECT id, iban, name, currency, bank_name, country
    FROM accounts
    WHERE bank_name = ? AND country = ?;
"""


class SqliteAccountRepository:
    """Concrete repository implementing Account persistence using SQLite."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_accounts(self, accounts: list[Account]) -> None:
        """Upsert accounts (inserts new ones and updates fields for existing ones)."""
        rows = [
            (acc.id, acc.iban, acc.name, acc.currency, acc.bank_name, acc.country)
            for acc in accounts
        ]
        with sqlite3.connect(self.__db_path) as conn:
            conn.executemany(_QUERY_SAVE, rows)

    def get_accounts(
        self, bank_name: str | None = None, country: str | None = None
    ) -> list[Account]:
        """Retrieve stored accounts, optionally filtered by bank and country."""
        base_query = "SELECT id, iban, name, currency, bank_name, country FROM accounts"
        where_clauses = []
        params = []

        if bank_name is not None:
            where_clauses.append("bank_name = ?")
            params.append(bank_name)
        if country is not None:
            where_clauses.append("country = ?")
            params.append(country)

        query = base_query
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Account(
                id=row[0],
                iban=row[1],
                name=row[2],
                currency=row[3],
                bank_name=row[4],
                country=row[5],
            )
            for row in rows
        ]
