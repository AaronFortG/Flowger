"""SQLAlchemy engine factory and table initialisation."""

from sqlmodel import SQLModel, create_engine


def make_engine(database_url: str):  # type: ignore[no-untyped-def]
    """Create a SQLAlchemy engine for the given URL.

    Tests pass "sqlite:///:memory:" to get a fresh in-memory database.
    Production uses the value from Settings.database_url.
    """
    return create_engine(database_url, echo=False)


def create_tables(database_url: str) -> None:
    """Create all SQLModel table-backed models in the target database.

    Safe to call multiple times (uses CREATE IF NOT EXISTS internally).
    The db_models module must be imported *before* this function is called
    so that SQLModel.metadata has the table definitions registered.
    """
    # Import here to ensure tables are registered before create_all.
    import flowger.infrastructure.db_models  # noqa: F401

    engine = make_engine(database_url)
    SQLModel.metadata.create_all(engine)
