import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from flowger.domain.bank_session import BankSession
from flowger.entrypoints.cli.main import app

_MODULE = "flowger.entrypoints.cli.commands.authorize"


@pytest.fixture()
def mock_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.database_path = str(tmp_path / "test.db")
    settings.default_bank = "Imagin"
    settings.default_country = "ES"
    return settings


def _make_session() -> BankSession:
    return BankSession(
        session_id="sess-abc",
        bank_name="Imagin",
        country="ES",
        created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    )


def test_authorize_happy_path(mock_settings: MagicMock) -> None:
    """Verify authorize orchestrates the code exchange and saving correctly."""
    session = _make_session()
    mock_sr = MagicMock()
    mock_ar = MagicMock()
    mock_provider = MagicMock()
    mock_provider.__enter__ = Mock(return_value=mock_provider)
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = (session, [])

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
        patch(f"{_MODULE}.SqliteSessionRepository", return_value=mock_sr),
        patch(f"{_MODULE}.SqliteAccountRepository", return_value=mock_ar),
        patch(f"{_MODULE}.create_bank_provider", return_value=mock_provider),
        patch(f"{_MODULE}.AuthorizeSessionUseCase", return_value=mock_use_case),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["authorize", "--code", "auth-code-123"])

    assert result.exit_code == 0
    assert "Session authorized" in result.output
    mock_use_case.execute.assert_called_once_with(
        code="auth-code-123", bank_name="Imagin", country="ES"
    )


def test_authorize_fails_fast_on_missing_bank_country(mock_settings: MagicMock) -> None:
    """Verify authorize fails when bank and country are missing from options and settings."""
    mock_settings.default_bank = None
    mock_settings.default_country = None

    with (
        patch(f"{_MODULE}.get_settings", return_value=mock_settings),
        patch(f"{_MODULE}.init_db"),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["authorize", "--code", "code-any"])

    assert result.exit_code == 1
    assert "Error: Bank and Country must be specified" in result.output
