from unittest.mock import Mock

from flowger.infrastructure.enable_banking.provider import EnableBankingProvider


def _make_provider() -> EnableBankingProvider:
    provider = EnableBankingProvider(
        app_id="dummy", private_key_path="dummy", environment="SANDBOX"
    )
    # Replace private client with a mock to avoid real HTTP calls
    mock_client = Mock()
    provider._EnableBankingProvider__client = mock_client  # type: ignore[attr-defined]
    return provider


def test_authorize_session_exchanges_code_for_session_id() -> None:
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.post.return_value = {"session_id": "sess-xyz789"}

    session = provider.authorize_session(code="auth-code-123", bank_name="Imagin", country="ES")

    assert session.session_id == "sess-xyz789"
    assert session.bank_name == "Imagin"
    assert session.country == "ES"
    mock_client.post.assert_called_once_with("/sessions", json={"code": "auth-code-123"})


def test_fetch_accounts_maps_response_to_domain() -> None:
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.get.return_value = {
        "accounts": [
            {
                "uid": "acc-1",
                "iban": "ES91 2100 0418 4502 0005 1332",
                "product": "Cuenta",
                "currency": "EUR",
            },
        ]
    }

    accounts = provider.fetch_accounts(session_id="sess-xyz789")

    assert len(accounts) == 1
    assert accounts[0].id == "acc-1"
    assert accounts[0].currency == "EUR"
    mock_client.get.assert_called_once_with("/accounts?session_id=sess-xyz789")
