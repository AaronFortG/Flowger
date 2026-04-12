import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.entrypoints.cli.main import app

_MODULE = "flowger.entrypoints.cli.commands.sync"


@pytest.fixture()
def mock_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")
    settings.bank = None
    settings.country = None
    settings.default_bank = "Imagin"
    settings.default_country = "ES"
    return settings


def _make_session() -> BankSession:
    return BankSession(
        session_id="sess-123",
        bank_name="Imagin",
        country="ES",
        created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    )


def _make_account() -> Account:
    return Account(
        id="acc-123",
        iban="ES001",
        name="Checking",
        currency="EUR",
        bank_name="Imagin",
        country="ES",
    )


def test_sync_happy_path(mock_settings: MagicMock) -> None:
    """Verify sync orchestrates the provider and use case correctly."""
    session = _make_session()
    account = _make_account()

    mock_sr = MagicMock()
    mock_sr.get_latest_session.return_value = session
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]
    mock_tr = MagicMock()
    mock_provider = MagicMock()
    mock_provider.__enter__ = Mock(return_value=mock_provider)
    mock_provider.__exit__ = Mock(return_value=False)
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = []  # No failures

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.create_bank_provider", return_value=mock_provider),
        patch(f"{_MODULE}.SyncTransactionsUseCase", return_value=mock_use_case),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["sync"])

    assert result.exit_code == 0
    assert "Transaction sync complete" in result.output
    mock_use_case.execute.assert_called_once()


def test_sync_fails_fast_on_missing_bank_country(mock_settings: MagicMock) -> None:
    """Verify sync fails when bank and country are missing from options and settings."""
    mock_settings.default_bank = None
    mock_settings.default_country = None

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["sync"])

    assert result.exit_code == 1
    assert "Error: Bank and Country must be specified" in result.output


def test_sync_fails_if_no_session(mock_settings: MagicMock) -> None:
    """Verify sync fails when no session is found locally for the bank/country."""
    mock_sr = MagicMock()
    mock_sr.get_latest_session.return_value = None

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["sync"])

    assert result.exit_code == 1
    assert "No session found" in result.output


def test_sync_fails_if_no_accounts(mock_settings: MagicMock) -> None:
    """Verify sync fails when no accounts are found locally for the bank/country."""
    session = _make_session()
    mock_sr = MagicMock()
    mock_sr.get_latest_session.return_value = session
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = []  # No accounts

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["sync"])

    assert result.exit_code == 1
    assert "No accounts found" in result.output
