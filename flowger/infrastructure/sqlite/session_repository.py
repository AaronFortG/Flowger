import datetime
import sqlite3

from flowger.application.session_repository import SessionRepository

# Use relative import for BankSession due to current package structure
from flowger.domain.bank_session import BankSession


class SqliteSessionRepository(SessionRepository):
    """Concrete repository persisting BankSession records using SQLite."""

    _TABLE_NAME = "sessions"
    _QUERY_SAVE = f"""
        INSERT INTO {_TABLE_NAME} (bank_name, country, session_id, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(bank_name, country) DO UPDATE SET
            session_id=excluded.session_id,
            created_at=excluded.created_at;
    """
    _QUERY_GET_LATEST = f"""
        SELECT session_id, created_at FROM {_TABLE_NAME}
        WHERE bank_name=? AND country=?
    """

    def __init__(self, db_path: str) -> None:
        self.__db_path = db_path

    def save_session(self, session: BankSession) -> None:
        """Upsert the session — only one session per (bank_name, country) is kept."""
        with sqlite3.connect(self.__db_path) as conn:
            conn.execute(
                self._QUERY_SAVE,
                (
                    session.bank_name,
                    session.country,
                    session.session_id,
                    session.created_at.isoformat(),
                ),
            )

    def get_latest_session(self, bank_name: str, country: str) -> BankSession | None:
        """Return the stored session for a bank, or None if not found."""
        with sqlite3.connect(self.__db_path) as conn:
            row = conn.execute(self._QUERY_GET_LATEST, (bank_name, country)).fetchone()

        if row is None:
            return None

        return BankSession(
            session_id=row[0],
            bank_name=bank_name,
            country=country,
            created_at=datetime.datetime.fromisoformat(row[1]),
        )
