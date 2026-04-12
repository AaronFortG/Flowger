import pytest
from pydantic import ValidationError

from flowger.infrastructure.config import Settings


def test_settings_validation_fails_without_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure validation fails when environment variables are missing."""
    # Ensure no environment variables are accidentally satisfying the model
    monkeypatch.delenv("ENABLEBANKING_APP_ID", raising=False)
    monkeypatch.delenv("ENABLEBANKING_KEY_PATH", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    # Only enablebanking_app_id is required; enablebanking_key_path has a default
    assert "enablebanking_app_id" in str(exc_info.value)


def test_settings_loads_valid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure settings load successfully with valid configuration."""
    monkeypatch.setenv("ENABLEBANKING_APP_ID", "test-app-id")
    monkeypatch.setenv("ENABLEBANKING_KEY_PATH", "/tmp/mock.key")

    settings = Settings(_env_file=None)

    assert settings.enablebanking_app_id == "test-app-id"
    assert settings.enablebanking_key_path == "/tmp/mock.key"


def test_settings_key_path_defaults_to_container_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure enablebanking_key_path defaults to /keys/private.pem when not set."""
    monkeypatch.setenv("ENABLEBANKING_APP_ID", "test-app-id")
    monkeypatch.delenv("ENABLEBANKING_KEY_PATH", raising=False)

    settings = Settings(_env_file=None)

    assert settings.enablebanking_key_path == "/keys/private.pem"
