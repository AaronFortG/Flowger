import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from flowger.domain.account import Account
from flowger.domain.bank_session import BankSession
from flowger.domain.exceptions import BankProviderError

_MODULE = "flowger.entrypoints.cli.commands.setup"


def _make_session() -> BankSession:
    return BankSession(
        session_id="sess-abc",
        bank_name="Imagin",
        country="ES",
        created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    )


def _make_accounts() -> list[Account]:
    return [Account(id="acc-1", iban="ES001", name="Imagin Checking", currency="EUR")]


@pytest.fixture()
def mock_settings(tmp_path: pytest.TempPathFactory) -> MagicMock:
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")
    settings.default_bank = "Imagin"
    settings.default_country = "ES"
    settings.default_redirect_url = "https://enablebanking.com/ais/"
    return settings


def _build_mocks(
    accounts: list[Account],
    session: BankSession,
    fetch_side_effect: object = None,
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    mock_provider = MagicMock()
    mock_provider.__enter__ = Mock(return_value=mock_provider)
    mock_provider.__exit__ = Mock(return_value=False)
    mock_provider.start_authorization.return_value = "https://auth.example.com/abc"
    mock_provider.authorize_session.return_value = (session, accounts)
    if fetch_side_effect is not None:
        mock_provider.fetch_transactions.side_effect = fetch_side_effect
    else:
        mock_provider.fetch_transactions.return_value = []

    mock_session_repo = MagicMock()
    mock_account_repo = MagicMock()
    mock_account_repo.get_accounts.return_value = accounts
    mock_transaction_repo = MagicMock()

    return mock_provider, mock_session_repo, mock_account_repo, mock_transaction_repo


def test_setup_happy_path(mock_settings: MagicMock) -> None:
    """Verify setup orchestrates auth URL, code exchange, sync, and account listing."""
    from typer.testing import CliRunner

    from flowger.entrypoints.cli.main import app

    session = _make_session()
    accounts = _make_accounts()
    mock_provider, mock_sr, mock_ar, mock_tr = _build_mocks(accounts, session)

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.create_bank_provider", return_value=mock_provider),
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch("typer.prompt", return_value="auth-code-123"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["setup", "--bank", "Imagin", "--country", "ES"])

    assert result.exit_code == 0, result.output
    assert "https://auth.example.com/abc" in result.output
    assert "Session authorized" in result.output
    assert "acc-1" in result.output
    assert "Setup complete" in result.output


def test_setup_with_sync_failures(mock_settings: MagicMock) -> None:
    """Verify setup prints a warning when the initial sync has failures."""
    from typer.testing import CliRunner

    from flowger.entrypoints.cli.main import app

    session = _make_session()
    accounts = _make_accounts()
    # SyncTransactionsUseCase catches BankProviderError — use that to simulate failure
    mock_provider, mock_sr, mock_ar, mock_tr = _build_mocks(
        accounts, session, fetch_side_effect=BankProviderError("API Error")
    )

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.create_bank_provider", return_value=mock_provider),
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.SqliteTransactionRepository", return_value=mock_tr),
        patch("typer.prompt", return_value="auth-code-xyz"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["setup"])

    assert result.exit_code == 0, result.output
    assert "failure" in result.output.lower()
