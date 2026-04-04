from unittest.mock import Mock

from flowger.infrastructure.enable_banking.provider import EnableBankingProvider


def test_start_authorization_returns_url() -> None:
    """Verify that start_authorization sends correct payload and extracts URL."""
    # 1. Arrange
    provider = EnableBankingProvider(
        app_id="dummy", private_key_path="dummy", environment="SANDBOX"
    )
    
    # We patch the private client to avoid hitting the real network
    mock_client = Mock()
    mock_client.post.return_value = {"url": "https://auth.enablebanking.com/abcd123"}
    provider._EnableBankingProvider__client = mock_client  # type: ignore[attr-defined]

    # 2. Act
    url = provider.start_authorization(
        bank_name="Imagin",
        country="ES",
        redirect_url="http://localhost:8000/callback"
    )

    # 3. Assert
    assert url == "https://auth.enablebanking.com/abcd123"
    
    # Verify the payload structure sent to the client
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/auth"
    payload = kwargs["json"]
    assert payload["aspsp"]["name"] == "Imagin"
    assert payload["aspsp"]["country"] == "ES"
    assert payload["redirect_url"] == "http://localhost:8000/callback"
