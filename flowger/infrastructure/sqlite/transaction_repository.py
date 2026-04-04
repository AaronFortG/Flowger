import sqlite3
from decimal import Decimal

from flowger.domain.transaction import Transaction

_QUERY_SAVE = """
    INSERT INTO transactions
    (id, account_id, date, amount, currency, description, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        date=excluded.date,
        amount=excluded.amount,
        currency=excluded.currency,
        description=excluded.description,
        notes=excluded.notes;
"""

_QUERY_GET_FOR_ACCOUNT = """
    SELECT id, account_id, date, amount, currency, description, notes
    FROM transactions
    WHERE account_id = ?
    ORDER BY date DESC;
"""


class SqliteTransactionRepository:
    """Concrete repository persisting Transaction records using SQLite."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_transactions(self, transactions: list[Transaction]) -> None:
        """Upsert transactions — inserts new ones and updates all mutable fields for existing IDs."""
        rows = [
            (
                tx.id,
                tx.account_id,
                tx.date.isoformat(),
                str(tx.amount),
                tx.currency,
                tx.description,
                tx.notes,
            )
            for tx in transactions
        ]
        with sqlite3.connect(self.__db_path) as conn:
            conn.executemany(_QUERY_SAVE, rows)

    def get_transactions_for_account(self, account_id: str) -> list[Transaction]:
        """Return all stored transactions for a given account, newest first."""
        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(_QUERY_GET_FOR_ACCOUNT, (account_id,)).fetchall()

        return [
            Transaction(
                id=row[0],
                account_id=row[1],
                date=row[2],
                amount=Decimal(row[3]),
                currency=row[4],
                description=row[5],
                notes=row[6],
            )
            for row in rows
        ]
