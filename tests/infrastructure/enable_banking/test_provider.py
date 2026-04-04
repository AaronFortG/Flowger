from unittest.mock import Mock

from flowger.infrastructure.enable_banking.client import EnableBankingClient
from flowger.infrastructure.enable_banking.provider import EnableBankingProvider


def _make_provider() -> EnableBankingProvider:
    """Create an EnableBankingProvider with a mock client injected, no real key needed."""
    mock_client = Mock(spec=EnableBankingClient)
    return EnableBankingProvider(
        app_id="dummy",
        private_key_path="dummy",
        environment="SANDBOX",
        client=mock_client,
    )


def test_start_authorization_returns_url() -> None:
    """Verify that start_authorization sends correct payload and extracts URL."""
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.post.return_value = {"url": "https://auth.enablebanking.com/abcd123"}

    url = provider.start_authorization(
        bank_name="Imagin",
        country="ES",
        redirect_url="http://localhost:8000/callback",
    )

    assert url == "https://auth.enablebanking.com/abcd123"

    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/auth"
    payload = kwargs["json"]
    assert payload["aspsp"]["name"] == "Imagin"
    assert payload["aspsp"]["country"] == "ES"
    assert payload["redirect_url"] == "http://localhost:8000/callback"


def test_start_authorization_missing_url() -> None:
    """Verify an empty string is returned when the API response has no 'url' field."""
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.post.return_value = {}  # 'url' key absent

    url = provider.start_authorization(
        bank_name="Imagin", country="ES", redirect_url="http://localhost:8000/callback"
    )

    assert url == ""
