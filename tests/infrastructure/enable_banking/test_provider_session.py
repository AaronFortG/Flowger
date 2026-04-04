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


def test_fetch_transactions_maps_response_to_domain() -> None:
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.get.return_value = {
        "transactions": [
            {
                "uid": "tx-1",
                "booking_date": "2026-04-01",
                "amount": "100.50",
                "currency": "EUR",
                "creditor_name": "Supermarket",
                "remittance_information_unstructured": "Weekly shop",
            }
        ]
    }

    transactions = provider.fetch_transactions(session_id="sess-xyz789", account_id="acc-1")

    assert len(transactions) == 1
    tx = transactions[0]
    assert tx.id == "tx-1"
    assert str(tx.amount) == "100.50"
    assert tx.description == "Supermarket"
    assert tx.notes == "Weekly shop"
    mock_client.get.assert_called_once_with(
        "/accounts/acc-1/transactions?session_id=sess-xyz789"
    )


def test_fetch_transactions_description_fallback() -> None:
    """Verify description falls back to remittance info when names are absent."""
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.get.return_value = {
        "transactions": [
            {
                "uid": "tx-2",
                "booking_date": "2026-04-01",
                "amount": "-30.00",
                "currency": "EUR",
                "remittance_information_unstructured": "Invoice 42",
            }
        ]
    }

    transactions = provider.fetch_transactions(session_id="sess-xyz789", account_id="acc-1")

    assert transactions[0].description == "Invoice 42"


def test_fetch_transactions_no_description_fallback() -> None:
    """Verify description defaults to 'No description' when all name fields are absent."""
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.get.return_value = {
        "transactions": [
            {
                "uid": "tx-3",
                "booking_date": "2026-04-01",
                "amount": "5.00",
                "currency": "EUR",
            }
        ]
    }

    transactions = provider.fetch_transactions(session_id="sess-xyz789", account_id="acc-1")

    assert transactions[0].description == "No description"
