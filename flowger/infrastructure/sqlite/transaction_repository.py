import sqlite3
from decimal import Decimal

from flowger.application.transaction_repository import TransactionRepository
from flowger.domain.transaction import Transaction


class SqliteTransactionRepository(TransactionRepository):
    """Concrete repository persisting Transaction records using SQLite."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_transactions(self, transactions: list[Transaction]) -> None:
        """Insert transactions, ignoring duplicates by primary key (id)."""
        query = """
        INSERT OR IGNORE INTO transactions (id, account_id, date, amount, currency, description)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        rows = [
            (tx.id, tx.account_id, tx.date.isoformat(), str(tx.amount), tx.currency, tx.description)
            for tx in transactions
        ]
        with sqlite3.connect(self.__db_path) as conn:
            conn.executemany(query, rows)

    def get_transactions_for_account(self, account_id: str) -> list[Transaction]:
        """Return all stored transactions for a given account, newest first."""
        query = """
        SELECT id, account_id, date, amount, currency, description
        FROM transactions
        WHERE account_id = ?
        ORDER BY date DESC;
        """
        with sqlite3.connect(self.__db_path) as conn:
            rows = conn.execute(query, (account_id,)).fetchall()

        return [
            Transaction(
                id=row[0],
                account_id=row[1],
                date=row[2],
                amount=Decimal(row[3]),
                currency=row[4],
                description=row[5],
            )
            for row in rows
        ]
