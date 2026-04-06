import sqlite3

_SCHEMA_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT NOT NULL,
    iban TEXT NOT NULL,
    name TEXT NOT NULL,
    currency TEXT NOT NULL,
    bank_name TEXT NOT NULL,
    country TEXT NOT NULL,
    PRIMARY KEY (bank_name, country, id)
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

_SCHEMA_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS transactions (
    id          TEXT NOT NULL,
    account_id  TEXT NOT NULL,
    bank_name   TEXT NOT NULL,
    country     TEXT NOT NULL,
    date        TEXT NOT NULL,
    amount      TEXT NOT NULL,
    currency    TEXT NOT NULL,
    payee       TEXT NOT NULL,
    notes       TEXT NOT NULL,
    exported_at TEXT,
    PRIMARY KEY (bank_name, country, account_id, id)
);
"""


def init_db(db_path: str) -> None:
    """Initialize the SQLite database schema."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(_SCHEMA_ACCOUNTS)
        conn.execute(_SCHEMA_SESSIONS)
        conn.execute(_SCHEMA_TRANSACTIONS)
