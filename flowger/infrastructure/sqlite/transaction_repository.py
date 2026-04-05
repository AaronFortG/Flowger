import sqlite3
from decimal import Decimal
from typing import Any

from flowger.domain.transaction import Transaction

_QUERY_SAVE = """
    INSERT INTO transactions
    (id, account_id, date, amount, currency, payee, notes, exported_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        account_id=excluded.account_id,
        date=excluded.date,
        amount=excluded.amount,
        currency=excluded.currency,
        payee=excluded.payee,
        notes=excluded.notes,
        exported_at=excluded.exported_at;
"""

_QUERY_GET_FOR_ACCOUNT = """
    SELECT id, account_id, date, amount, currency, payee, notes, exported_at
    FROM transactions
    WHERE account_id = ?
    ORDER BY date DESC;
"""

_QUERY_GET_UNEXPORTED = """
    SELECT id, account_id, date, amount, currency, payee, notes, exported_at
    FROM transactions
    WHERE account_id = ? AND exported_at IS NULL
    ORDER BY date DESC;
"""


class SqliteTransactionRepository:
    """Concrete repository persisting Transaction records using SQLite."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_transactions(self, transactions: list[Transaction]) -> None:
        """Upsert transactions — inserts new ones and updates existing ones completely."""
        rows = [
            (
                tx.id,
                tx.account_id,
                tx.date.isoformat(),
                str(tx.amount),
                tx.currency,
                tx.payee,
                tx.notes,
                tx.exported_at.isoformat() if tx.exported_at else None,
            )
            for tx in transactions
        ]
        with sqlite3.connect(self.__db_path) as conn:
            conn.executemany(_QUERY_SAVE, rows)

    def get_transactions_for_account(self, account_id: str) -> list[Transaction]:
        """Return all stored transactions for a given account, newest first."""
        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(_QUERY_GET_FOR_ACCOUNT, (account_id,)).fetchall()
        return self.__map_rows(rows)

    def get_unexported_transactions(self, account_id: str) -> list[Transaction]:
        """Return all transactions for an account that have never been exported."""
        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(_QUERY_GET_UNEXPORTED, (account_id,)).fetchall()
        return self.__map_rows(rows)

    def __map_rows(self, rows: list[Any]) -> list[Transaction]:
        from datetime import date, datetime

        return [
            Transaction(
                id=row[0],
                account_id=row[1],
                date=date.fromisoformat(row[2]),
                amount=Decimal(row[3]),
                currency=row[4],
                payee=row[5],
                notes=row[6],
                exported_at=datetime.fromisoformat(row[7]) if row[7] else None,
            )
            for row in rows
        ]
