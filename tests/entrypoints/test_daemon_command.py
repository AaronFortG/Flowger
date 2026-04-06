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
    return settings


def test_daemon_fails_fast_on_missing_accounts(mock_settings: MagicMock) -> None:
    """Verify daemon fails fast if no accounts exist for the specified bank/country."""
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [] # No accounts

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
    ):
        runner = CliRunner()
        result = runner.invoke(
            app, ["daemon", "--bank", "Imagin", "--country", "ES", "--cron", "0 3 * * *"]
        )

    assert result.exit_code == 1
    assert "Error: No accounts found for Imagin (ES)" in result.output


def test_daemon_fails_on_missing_options(mock_settings: MagicMock) -> None:
    """Verify daemon fails when bank and country are missing (they are required for daemon)."""
    # Note: Typer enforces --bank and --country as mandatory via '...' in Option
    # but let's see how it behaves when they are not passed and not in settings.
    mock_settings.default_bank = None
    mock_settings.default_country = None

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["daemon"]) # Missing options

    # Typer's error message for missing mandatory option
    assert result.exit_code != 0
    assert "Missing option" in result.output
