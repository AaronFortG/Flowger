import sqlite3
from decimal import Decimal

from flowger.application.transaction_repository import TransactionRepository
from flowger.domain.transaction import Transaction


class SqliteTransactionRepository(TransactionRepository):
    """Concrete repository persisting Transaction records using SQLite."""

    _TABLE_NAME = "transactions"
    _QUERY_SAVE = f"""
        INSERT INTO {_TABLE_NAME}
        (id, account_id, date, amount, currency, description, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            date=excluded.date,
            amount=excluded.amount,
            description=excluded.description,
            notes=excluded.notes;
    """
    _QUERY_GET_FOR_ACCOUNT = f"""
        SELECT id, account_id, date, amount, currency, description, notes
        FROM {_TABLE_NAME}
        WHERE account_id = ?
        ORDER BY date DESC;
    """

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_transactions(self, transactions: list[Transaction]) -> None:
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
            conn.executemany(self._QUERY_SAVE, rows)

    def get_transactions_for_account(self, account_id: str) -> list[Transaction]:
        """Return all stored transactions for a given account, newest first."""
        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(self._QUERY_GET_FOR_ACCOUNT, (account_id,)).fetchall()

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
