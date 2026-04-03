"""SQLite implementation of TransactionRepository using SQLModel."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import desc
from sqlmodel import Session, select

from flowger.domain.models import Account, Transaction
from flowger.domain.ports import TransactionRepository
from flowger.infrastructure.db_models import AccountTable, TransactionTable


class SQLiteTransactionRepository(TransactionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    def save_account(self, account: Account) -> None:
        """Insert or update an account (upsert via merge)."""
        db_row = AccountTable(
            id=account.id,
            name=account.name,
            currency=account.currency,
            provider=account.provider,
            iban=account.iban,
        )
        self._session.merge(db_row)
        self._session.commit()

    def get_accounts(self) -> list[Account]:
        rows = self._session.exec(select(AccountTable)).all()
        return [_row_to_account(r) for r in rows]

    def get_account(self, account_id: str) -> Account | None:
        row = self._session.get(AccountTable, account_id)
        return _row_to_account(row) if row else None

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def upsert_transactions(self, transactions: list[Transaction]) -> int:
        """Insert only transactions not yet stored (idempotent by ID).

        Returns the number of newly inserted records.
        """
        new_count = 0
        for tx in transactions:
            if self._session.get(TransactionTable, tx.id) is None:
                self._session.add(
                    TransactionTable(
                        id=tx.id,
                        account_id=tx.account_id,
                        date=tx.date,
                        amount=tx.amount,
                        currency=tx.currency,
                        description=tx.description,
                        reference=tx.reference,
                        created_at=tx.created_at,
                    )
                )
                new_count += 1
        self._session.commit()
        return new_count

    def get_transactions(self, account_id: str) -> list[Transaction]:
        rows = self._session.exec(
            select(TransactionTable)
            .where(TransactionTable.account_id == account_id)
            .order_by(TransactionTable.date)  # type: ignore[arg-type]
        ).all()
        return [_row_to_transaction(r) for r in rows]

    def get_last_sync_date(self, account_id: str) -> date | None:
        rows = self._session.exec(
            select(TransactionTable)
            .where(TransactionTable.account_id == account_id)
            .order_by(desc(TransactionTable.date))  # type: ignore[arg-type]
            .limit(1)
        ).all()
        return rows[0].date if rows else None


# ------------------------------------------------------------------
# Private mapping helpers
# ------------------------------------------------------------------


def _row_to_account(row: AccountTable) -> Account:
    return Account(
        id=row.id,
        name=row.name,
        currency=row.currency,
        provider=row.provider,
        iban=row.iban,
    )


def _row_to_transaction(row: TransactionTable) -> Transaction:
    return Transaction(
        id=row.id,
        account_id=row.account_id,
        date=row.date,
        amount=Decimal(str(row.amount)),
        currency=row.currency,
        description=row.description,
        reference=row.reference,
        created_at=row.created_at or datetime.now(UTC),
    )
