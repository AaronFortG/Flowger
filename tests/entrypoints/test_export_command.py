from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from flowger.domain.account import Account
from flowger.entrypoints.cli.main import app

_MODULE = "flowger.entrypoints.cli.commands.export"


@pytest.fixture()
def mock_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")
    settings.default_bank = "Imagin"
    settings.default_country = "ES"
    settings.default_export_file = str(tmp_path / "export.csv")
    return settings


def _make_account() -> Account:
    return Account(
        id="acc-123",
        iban="ES001",
        name="Checking",
        currency="EUR",
        bank_name="Imagin",
        country="ES",
    )


def test_export_happy_path(mock_settings: MagicMock) -> None:
    """Verify export orchestrates the use case correctly."""
    account = _make_account()
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]
    mock_tr = MagicMock()
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = 5  # Exported 5 transactions

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.ExportTransactionsUseCase", return_value=mock_use_case),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["export", "--account-id", "acc-123"])

    assert result.exit_code == 0
    assert "Export complete. 5 transaction(s) saved" in result.output
    mock_use_case.execute.assert_called_once()


def test_export_fails_fast_on_missing_bank_country(mock_settings: MagicMock) -> None:
    """Verify export fails when bank and country are missing from options and settings."""
    mock_settings.default_bank = None
    mock_settings.default_country = None

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["export", "--account-id", "any"])

    assert result.exit_code == 1
    assert "Error: Bank and Country must be specified" in result.output


def test_export_fails_if_account_id_not_found(mock_settings: MagicMock) -> None:
    """Verify export fails when the requested account ID doesn't exist in either table."""
    account = _make_account()
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]  # Return one account, but not the one requested
    mock_tr = MagicMock()
    mock_tr.has_transactions.return_value = False  # No transactions either

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["export", "--account-id", "non-existent"])

    assert result.exit_code == 1
    assert "Error: Account ID 'non-existent' not found" in result.output
    assert "Available accounts for this bank/country" in result.output
    assert "acc-123" in result.output
    assert "Checking" in result.output


def test_export_works_with_orphan_transactions(mock_settings: MagicMock) -> None:
    """Verify export works when no account record exists but transactions are present."""
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = []  # Missing account record

    mock_tr = MagicMock()
    mock_tr.has_transactions.return_value = True  # Transactions exist

    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = 1

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.ExportTransactionsUseCase", return_value=mock_use_case),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["export", "--account-id", "missing-acc"])

    assert result.exit_code == 0
    assert "Export complete. 1 transaction(s) saved" in result.output


def test_export_no_transactions_found(mock_settings: MagicMock) -> None:
    """Verify export prints a yellow message when no transactions are found."""
    account = _make_account()
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]
    mock_tr = MagicMock()
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = 0  # No transactions exported

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.ExportTransactionsUseCase", return_value=mock_use_case),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["export", "--account-id", "acc-123"])

    assert result.exit_code == 0
    assert "No transactions found for account acc-123" in result.output


def test_export_no_new_transactions_found(mock_settings: MagicMock) -> None:
    """Verify export prints a yellow message with 'new' qualifier when --new-only is used."""
    account = _make_account()
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]
    mock_tr = MagicMock()
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = 0  # No new transactions exported

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.ExportTransactionsUseCase", return_value=mock_use_case),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["export", "--account-id", "acc-123", "--new-only"])

    assert result.exit_code == 0
    assert "No new transactions found for account acc-123" in result.output
