import datetime
import sqlite3

from flowger.application.repositories import AccountRepository
from flowger.application.session_repository import SessionRepository
from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession

_SCHEMA_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    iban TEXT NOT NULL,
    name TEXT NOT NULL,
    currency TEXT NOT NULL
);
"""

_SCHEMA_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    bank_name TEXT NOT NULL,
    country   TEXT NOT NULL,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (bank_name, country)
);
"""


def init_db(db_path: str) -> None:
    """Initialize the SQLite database schema."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(_SCHEMA_ACCOUNTS)
        conn.execute(_SCHEMA_SESSIONS)


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


class SqliteSessionRepository(SessionRepository):
    """Concrete repository persisting BankSession records using SQLite."""

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_session(self, session: BankSession) -> None:
        """Upsert the session — only one session per (bank_name, country) is kept."""
        query = """
        INSERT INTO sessions (bank_name, country, session_id, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(bank_name, country) DO UPDATE SET
            session_id=excluded.session_id,
            created_at=excluded.created_at;
        """
        with sqlite3.connect(self.__db_path) as conn:
            conn.execute(
                query,
                (
                    session.bank_name,
                    session.country,
                    session.session_id,
                    session.created_at.isoformat(),
                ),
            )

    def get_latest_session(self, bank_name: str, country: str) -> BankSession | None:
        """Return the stored session for a bank, or None if not found."""
        query = "SELECT session_id, created_at FROM sessions WHERE bank_name=? AND country=?"
        with sqlite3.connect(self.__db_path) as conn:
            row = conn.execute(query, (bank_name, country)).fetchone()

        if row is None:
            return None

        return BankSession(
            session_id=row[0],
            bank_name=bank_name,
            country=country,
            created_at=datetime.datetime.fromisoformat(row[1]),
        )
