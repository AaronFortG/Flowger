import datetime
from pathlib import Path

import pytest

from flowger.domain.bank_session import BankSession
from flowger.infrastructure.sqlite import SqliteSessionRepository, init_db


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


def _make_session(**kwargs: object) -> BankSession:
    defaults: dict[str, object] = {
        "session_id": "sess-abc123",
        "bank_name": "Imagin",
        "country": "ES",
        "created_at": datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    }
    defaults.update(kwargs)
    return BankSession(**defaults)


def test_save_and_retrieve_session(db_path: str) -> None:
    repo = SqliteSessionRepository(db_path)
    session = _make_session()

    repo.save_session(session)

    retrieved = repo.get_latest_session("Imagin", "ES")
    assert retrieved is not None
    assert retrieved.session_id == "sess-abc123"
    assert retrieved.bank_name == "Imagin"
    assert retrieved.country == "ES"


def test_save_session_upserts(db_path: str) -> None:
    """Saving a second session for the same bank should overwrite the first."""
    repo = SqliteSessionRepository(db_path)
    repo.save_session(_make_session(session_id="old-session"))
    repo.save_session(_make_session(session_id="new-session"))

    result = repo.get_latest_session("Imagin", "ES")
    assert result is not None
    assert result.session_id == "new-session"


def test_get_latest_session_returns_none_when_missing(db_path: str) -> None:
    repo = SqliteSessionRepository(db_path)
    result = repo.get_latest_session("NonExistent", "XX")
    assert result is None
