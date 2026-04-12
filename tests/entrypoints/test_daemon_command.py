from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from flowger.entrypoints.cli.main import app

_MODULE = "flowger.entrypoints.cli.commands.daemon"


@pytest.fixture()
def mock_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")
    settings.default_bank = "Imagin"
    settings.default_country = "ES"
    settings.sync_cron = "0 3 * * *"
    return settings


def test_daemon_triggers_setup_when_no_accounts(mock_settings: MagicMock) -> None:
    """Verify daemon starts interactive setup when no accounts exist."""
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = []  # No accounts

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}._run_setup", return_value=None) as mock_setup,
    ):
        runner = CliRunner()
        result = runner.invoke(
            app, ["daemon", "--bank", "Imagin", "--country", "ES", "--cron", "0 3 * * *"]
        )

    assert result.exit_code == 1
    assert "Setup was not completed" in result.output
    mock_setup.assert_called_once()


def test_daemon_starts_normally_when_accounts_exist(mock_settings: MagicMock) -> None:
    """Verify daemon enters cron loop when accounts already exist."""
    mock_account = MagicMock()
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [mock_account]

    mock_sr = MagicMock()
    mock_session = MagicMock()
    mock_session.session_id = "sess-123"
    mock_sr.get_latest_session.return_value = mock_session

    mock_tr = MagicMock()

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.time.sleep", side_effect=KeyboardInterrupt),
        patch(f"{_MODULE}._run_sync"),
    ):
        runner = CliRunner()
        result = runner.invoke(
            app, ["daemon", "--bank", "Imagin", "--country", "ES", "--cron", "0 3 * * *"]
        )

    assert result.exit_code == 0
    assert "Found 1 account(s) for Imagin (ES)" in result.output
    assert "Starting Flowger daemon" in result.output


def test_daemon_fails_on_missing_bank_country(mock_settings: MagicMock) -> None:
    """Verify daemon fails when bank/country are not configured."""
    mock_settings.default_bank = None
    mock_settings.default_country = None
    mock_settings.bank = None
    mock_settings.country = None

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["daemon", "--cron", "0 3 * * *"])
        assert result.exit_code == 1
        assert "Error: Bank and Country must be specified" in result.output


def test_daemon_fails_on_invalid_cron(mock_settings: MagicMock) -> None:
    """Verify daemon fails when cron expression is invalid."""
    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
    ):
        runner = CliRunner()
        result = runner.invoke(
            app, ["daemon", "--bank", "Imagin", "--country", "ES", "--cron", "not-a-cron"]
        )
        assert result.exit_code == 1
        assert "Invalid cron expression" in result.output
