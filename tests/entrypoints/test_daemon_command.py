from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from typer.testing import CliRunner

from flowger.domain.account import Account
from flowger.entrypoints.cli.commands.daemon import _run_export, _run_sync
from flowger.entrypoints.cli.main import app

_MODULE = "flowger.entrypoints.cli.commands.daemon"


@pytest.fixture()
def mock_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")
    settings.default_bank = "Imagin"
    settings.default_country = "ES"
    settings.sync_cron = "0 3 * * *"
    settings.default_export_file = str(tmp_path / "exports" / "transactions.csv")
    return settings


def _make_account(account_id: str = "acc-123") -> Account:
    return Account(
        id=account_id,
        iban="ES001",
        name="Checking",
        currency="EUR",
        bank_name="Imagin",
        country="ES",
    )


# ── daemon command integration tests ─────────────────────────────────────────


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


# ── _run_sync unit tests ──────────────────────────────────────────────────────


def test_run_sync_returns_false_when_no_session(mock_settings: MagicMock) -> None:
    """_run_sync should abort and return False when no session is stored."""
    mock_sr = MagicMock()
    mock_sr.get_latest_session.return_value = None

    with (
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository"),
        patch(f"{_MODULE}.SqliteTransactionRepository"),
    ):
        result = _run_sync("Imagin", "ES", mock_settings)

    assert result is False


def test_run_sync_returns_false_when_no_accounts(mock_settings: MagicMock) -> None:
    """_run_sync should abort and return False when no accounts exist for the bank/country."""
    mock_sr = MagicMock()
    mock_sr.get_latest_session.return_value = MagicMock(session_id="sess-1")
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = []

    with (
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository"),
    ):
        result = _run_sync("Imagin", "ES", mock_settings)

    assert result is False


def test_run_sync_happy_path_calls_export(mock_settings: MagicMock) -> None:
    """_run_sync returns True after a successful sync and triggers _run_export."""
    account = _make_account()
    mock_sr = MagicMock()
    mock_sr.get_latest_session.return_value = MagicMock(session_id="sess-1")
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]
    mock_tr = MagicMock()
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = []  # No failures

    with (
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.create_bank_provider") as mock_provider_ctx,
        patch(f"{_MODULE}.SyncTransactionsUseCase", return_value=mock_use_case),
        patch(f"{_MODULE}._run_export") as mock_export,
    ):
        mock_provider_ctx.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_provider_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = _run_sync("Imagin", "ES", mock_settings)

    assert result is True
    mock_export.assert_called_once_with([account], "Imagin", "ES", mock_settings)


def test_run_sync_returns_false_on_sync_failures(mock_settings: MagicMock) -> None:
    """_run_sync returns False (and skips export) when the sync use case reports failures."""
    account = _make_account()
    mock_sr = MagicMock()
    mock_sr.get_latest_session.return_value = MagicMock(session_id="sess-1")
    mock_ar = MagicMock()
    mock_ar.get_accounts.return_value = [account]
    mock_tr = MagicMock()
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = ["error"]  # One failure

    with (
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.create_bank_provider") as mock_provider_ctx,
        patch(f"{_MODULE}.SyncTransactionsUseCase", return_value=mock_use_case),
        patch(f"{_MODULE}._run_export") as mock_export,
    ):
        mock_provider_ctx.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_provider_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = _run_sync("Imagin", "ES", mock_settings)

    assert result is False
    mock_export.assert_not_called()


# ── _run_export unit tests ────────────────────────────────────────────────────


def test_run_export_writes_per_account_csv(mock_settings: MagicMock, tmp_path: Path) -> None:
    """_run_export invokes the use case once per account with a per-account output path."""
    acc1 = _make_account("acc-1")
    acc2 = _make_account("acc-2")
    mock_settings.default_export_file = str(tmp_path / "exports" / "transactions.csv")
    mock_tr = MagicMock()
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = 3

    with (
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.ExportTransactionsUseCase", return_value=mock_use_case),
    ):
        _run_export([acc1, acc2], "Imagin", "ES", mock_settings)

    assert mock_use_case.execute.call_count == 2
    calls = mock_use_case.execute.call_args_list
    assert calls[0] == call(
        account_id="acc-1",
        bank_name="Imagin",
        country="ES",
        output_path=str(tmp_path / "exports" / "acc-1.csv"),
    )
    assert calls[1] == call(
        account_id="acc-2",
        bank_name="Imagin",
        country="ES",
        output_path=str(tmp_path / "exports" / "acc-2.csv"),
    )


def test_run_export_skips_empty_accounts(mock_settings: MagicMock, tmp_path: Path) -> None:
    """_run_export prints a skip message when the use case returns 0 transactions."""
    acc = _make_account("acc-empty")
    mock_settings.default_export_file = str(tmp_path / "exports" / "transactions.csv")
    mock_tr = MagicMock()
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = 0  # Nothing to export

    with (
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch(f"{_MODULE}.ExportTransactionsUseCase", return_value=mock_use_case),
    ):
        # Should complete without error even when count is 0
        _run_export([acc], "Imagin", "ES", mock_settings)

    mock_use_case.execute.assert_called_once()
