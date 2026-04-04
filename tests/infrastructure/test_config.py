import pytest
from pydantic import ValidationError
from flowger.infrastructure.config import Settings, get_settings


def test_settings_validation_fails_without_required_env(monkeypatch):
    """Ensure validation fails when environment variables are missing."""
    # Ensure no environment variables are accidentally satisfying the model
    monkeypatch.delenv("ENABLEBANKING_APP_ID", raising=False)
    monkeypatch.delenv("ENABLEBANKING_ENVIRONMENT", raising=False)
    monkeypatch.delenv("ENABLEBANKING_KEY_PATH", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "enablebanking_app_id" in str(exc_info.value)
    assert "enablebanking_environment" in str(exc_info.value)
    assert "enablebanking_key_path" in str(exc_info.value)


def test_settings_loads_valid_env(monkeypatch):
    """Ensure settings load successfully with valid configuration."""
    monkeypatch.setenv("ENABLEBANKING_APP_ID", "test-app-id")
    monkeypatch.setenv("ENABLEBANKING_ENVIRONMENT", "SANDBOX")
    monkeypatch.setenv("ENABLEBANKING_KEY_PATH", "/tmp/mock.key")

    settings = Settings()
    
    assert settings.enablebanking_app_id == "test-app-id"
    assert settings.enablebanking_environment == "SANDBOX"
    assert settings.enablebanking_key_path == "/tmp/mock.key"
