"""Shared pytest fixtures."""

import pytest
from sqlmodel import Session, SQLModel, create_engine

# Import table models so SQLModel.metadata knows about them before create_all.
import flowger.infrastructure.db_models  # noqa: F401
from flowger.infrastructure.repositories import SQLiteTransactionRepository


@pytest.fixture()
def engine():
    """Fresh in-memory SQLite engine for each test."""
    _engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(_engine)
    yield _engine
    SQLModel.metadata.drop_all(_engine)


@pytest.fixture()
def session(engine):
    """SQLModel session bound to the in-memory engine."""
    with Session(engine) as _session:
        yield _session


@pytest.fixture()
def repository(session):
    """SQLiteTransactionRepository backed by the in-memory session."""
    return SQLiteTransactionRepository(session)
