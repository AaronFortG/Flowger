import sqlite3

_SCHEMA_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    iban TEXT NOT NULL,
    name TEXT NOT NULL,
    currency TEXT NOT NULL,
    bank_name TEXT NOT NULL,
    country TEXT NOT NULL
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
    id          TEXT PRIMARY KEY,
    account_id  TEXT NOT NULL,
    date        TEXT NOT NULL,
    amount      TEXT NOT NULL,
    currency    TEXT NOT NULL,
    payee       TEXT NOT NULL,
    notes       TEXT NOT NULL,
    exported_at TEXT
);
"""


def init_db(db_path: str) -> None:
    """Initialize the SQLite database schema."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(_SCHEMA_ACCOUNTS)
        conn.execute(_SCHEMA_SESSIONS)
        conn.execute(_SCHEMA_TRANSACTIONS)

        # Migration: Add bank_name and country if they don't exist
        cursor = conn.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in cursor.fetchall()]
        if "bank_name" not in columns:
            conn.execute("ALTER TABLE accounts ADD COLUMN bank_name TEXT NOT NULL DEFAULT ''")
        if "country" not in columns:
            conn.execute("ALTER TABLE accounts ADD COLUMN country TEXT NOT NULL DEFAULT ''")

        # Legacy check: if rows exist but bank_name is empty, warn the user.
        res = conn.execute("SELECT COUNT(*) FROM accounts WHERE bank_name = ''").fetchone()
        if res and res[0] > 0:
            import sys
            print(
                f"\n[WARNING] Found {res[0]} legacy accounts with missing "
                "bank info in the database.\n"
                "Please run 'flowger setup' for each bank to re-authorize "
                "and correctly scope these accounts.\n",
                file=sys.stderr
            )
