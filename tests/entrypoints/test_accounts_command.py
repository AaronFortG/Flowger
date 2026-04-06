from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from flowger.domain.account import Account
from flowger.entrypoints.cli.main import app

_MODULE = "flowger.entrypoints.cli.commands.accounts"


def test_accounts_list_all(tmp_path: Path) -> None:
    """Verify accounts command lists all accounts when no filters are provided."""
    account = Account(
        id="acc-123",
        iban="ES123",
        name="Test Account",
        currency="EUR",
        bank_name="TestBank",
        country="ES",
    )
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")

    with (
        patch(f"{_MODULE}.get_settings", return_value=settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["accounts"])

    assert result.exit_code == 0
    assert "acc-123" in result.output
    assert "Test Account" in result.output
    mock_ar.get_accounts.assert_called_once_with(bank_name=None, country=None)


def test_accounts_with_filters(tmp_path: Path) -> None:
    """Verify accounts command applies bank and country filters."""
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = []
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")

    with (
        patch(f"{_MODULE}.get_settings", return_value=settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["accounts", "--bank", "Imagin", "--country", "ES"])

    assert result.exit_code == 0
    assert "No accounts found for Imagin (ES)" in result.output
    mock_ar.get_accounts.assert_called_once_with(bank_name="Imagin", country="ES")
