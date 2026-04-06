from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from flowger.entrypoints.cli.main import app

_MODULE = "flowger.entrypoints.cli.commands.login"


@pytest.fixture()
def mock_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")
    settings.default_bank = "Imagin"
    settings.default_country = "ES"
    settings.default_redirect_url = "https://auth"
    return settings


def test_login_happy_path(mock_settings: MagicMock) -> None:
    """Verify login prints the authorization URL."""
    mock_provider = MagicMock()
    mock_provider.__enter__ = Mock(return_value=mock_provider)
    mock_provider.start_authorization.return_value = "https://magic-url"

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.create_bank_provider", return_value=mock_provider),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["login"])

    assert result.exit_code == 0
    assert "https://magic-url" in result.output
    mock_provider.start_authorization.assert_called_once()


def test_login_fails_fast_on_missing_bank_country(mock_settings: MagicMock) -> None:
    """Verify login fails when bank and country are missing from options and settings."""
    mock_settings.default_bank = None
    mock_settings.default_country = None

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["login"])

    assert result.exit_code == 1
    assert "Error: Bank and Country must be specified" in result.output
