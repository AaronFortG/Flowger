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


def test_authorize_session_exchanges_code_for_session_id_and_returns_accounts() -> None:
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.post.return_value = {
        "session_id": "sess-xyz789",
        "accounts": [
            {
                "uid": "acc-1",
                "account_id": {"iban": "ES00000000001"},
                "name": "Checking Account",
                "currency": "EUR",
            }
        ],
        "aspsp": {"name": "ImaginBank"}
    }

    session, accounts = provider.authorize_session(code="auth-code-123", bank_name="Imagin", country="ES")

    assert session.session_id == "sess-xyz789"
    assert session.bank_name == "Imagin"
    assert session.country == "ES"
    mock_client.post.assert_called_once_with("/sessions", json={"code": "auth-code-123"})
    
    assert len(accounts) == 1
    assert accounts[0].id == "acc-1"
    assert accounts[0].iban == "ES00000000001"
    assert accounts[0].name == "ImaginBank Checking Account"
    assert accounts[0].currency == "EUR"


def test_fetch_transactions_maps_response_to_domain() -> None:
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.get.return_value = {
        "transactions": [
            {
                "entry_reference": "tx-1",
                "booking_date": "2026-04-01",
                "amount": "100.50",
                "credit_debit_indicator": "DBIT",
                "currency": "EUR",
                "creditor": {"name": "Supermarket"},
                "remittance_information_unstructured": "Weekly shop",
            }
        ]
    }

    transactions = provider.fetch_transactions(session_id="sess-xyz789", account_id="acc-1")

    assert len(transactions) == 1
    tx = transactions[0]
    assert tx.id == "tx-1"
    assert str(tx.amount) == "-100.50"
    assert tx.payee == "Supermarket"
    assert tx.notes == "Weekly shop"
    mock_client.get.assert_called_once_with(
        "/accounts/acc-1/transactions?session_id=sess-xyz789"
    )


def test_fetch_transactions_payee_fallback() -> None:
    """Verify payee falls back to remittance info when names are absent."""
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.get.return_value = {
        "transactions": [
            {
                "entry_reference": "tx-2",
                "booking_date": "2026-04-01",
                "amount": "-30.00",
                "credit_debit_indicator": "DBIT",
                "currency": "EUR",
                "remittance_information_unstructured": "Invoice 42",
            }
        ]
    }

    transactions = provider.fetch_transactions(session_id="sess-xyz789", account_id="acc-1")

    assert transactions[0].payee == "Invoice 42"


def test_fetch_transactions_no_payee_fallback() -> None:
    """Verify payee defaults to 'No payee' when all name fields are absent."""
    provider = _make_provider()
    mock_client = provider._EnableBankingProvider__client  # type: ignore[attr-defined]
    mock_client.get.return_value = {
        "transactions": [
            {
                "entry_reference": "tx-3",
                "booking_date": "2026-04-01",
                "amount": "5.00",
                "currency": "EUR",
            }
        ]
    }

    transactions = provider.fetch_transactions(session_id="sess-xyz789", account_id="acc-1")

    assert transactions[0].payee == "Unknown Payee"
