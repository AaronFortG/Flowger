from unittest.mock import Mock

from flowger.infrastructure.enable_banking.client import EnableBankingClient
from flowger.infrastructure.enable_banking.provider import EnableBankingProvider


def _make_provider() -> tuple[EnableBankingProvider, Mock]:
    """Create an EnableBankingProvider with a mock client injected, no real key needed."""
    mock_client = Mock(spec=EnableBankingClient)
    return EnableBankingProvider(
        app_id="dummy",
        private_key_path="dummy",
        client=mock_client,
    ), mock_client


def test_start_authorization_returns_url() -> None:
    """Verify that start_authorization sends correct payload and extracts URL."""
    provider, mock_client = _make_provider()
    mock_client.post.return_value = {"url": "https://auth.enablebanking.com/abcd123"}

    url = provider.start_authorization(
        bank_name="Imagin",
        country="ES",
        redirect_url="http://localhost:8000/callback",
        state="mock_state",
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
    provider, mock_client = _make_provider()
    mock_client.post.return_value = {}  # 'url' key absent

    url = provider.start_authorization(
        bank_name="Imagin",
        country="ES",
        redirect_url="http://localhost:8000/callback",
        state="mock_state",
    )

    assert url == ""


def test_authorize_session_exchanges_code_for_session_id_and_returns_accounts() -> None:
    provider, mock_client = _make_provider()
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
        "aspsp": {"name": "ImaginBank"},
    }

    session, accounts = provider.authorize_session(
        code="auth-code-123", bank_name="Imagin", country="ES"
    )

    assert session.session_id == "sess-xyz789"
    assert session.bank_name == "Imagin"
    assert session.country == "ES"
    mock_client.post.assert_called_once_with("/sessions", json={"code": "auth-code-123"})

    assert len(accounts) == 1
    assert accounts[0].id == "acc-1"
    assert accounts[0].iban == "ES00000000001"
    assert accounts[0].name == "ImaginBank Checking Account"
    assert accounts[0].currency == "EUR"
    assert accounts[0].bank_name == "Imagin"
    assert accounts[0].country == "ES"


def test_authorize_session_account_name_fallbacks() -> None:
    """Verify that account extraction falls back to 'details' when 'name' is missing/empty."""
    provider, mock_client = _make_provider()
    mock_client.post.return_value = {
        "session_id": "sess-fallback",
        "accounts": [
            {
                "uid": "acc-details",
                "account_id": {"iban": "ES00000000002"},
                "name": " ",  # Empty string after stripping
                "details": "Checking Backup",
                "currency": "EUR",
            },
            {
                "uid": "acc-missing-key",
                "account_id": {"iban": "ES00000000003"},
                # 'name' key is completely missing
                "details": "Savings Account",
                "currency": "EUR",
            }
        ],
        "aspsp": {"name": "ImaginBank"},
    }

    _, accounts = provider.authorize_session(
        code="code-2", bank_name="Imagin", country="ES"
    )

    assert len(accounts) == 2
    # Should fall back to "details" because "name" is blank
    assert accounts[0].name == "ImaginBank Checking Backup"
    # Should fall back to "details" because 'name' key is missing
    assert accounts[1].name == "ImaginBank Savings Account"


def test_authorize_session_nested_iban_extraction() -> None:
    """Verify that IBAN is correctly extracted from the nested account_id object."""
    provider, mock_client = _make_provider()
    mock_client.post.return_value = {
        "session_id": "sess-iban",
        "accounts": [
            {
                "uid": "acc-iban",
                "account_id": {"iban": "ES1234567890"},
                "name": "IBAN Account",
                "currency": "EUR",
            }
        ],
        "aspsp": {"name": "TestBank"},
    }

    _, accounts = provider.authorize_session(
        code="code-3", bank_name="TestBank", country="ES"
    )

    assert len(accounts) == 1
    assert accounts[0].iban == "ES1234567890"


def test_authorize_session_other_identification_fallback() -> None:
    """Verify that extraction falls back to 'other.identification' when IBAN is missing."""
    provider, mock_client = _make_provider()
    mock_client.post.return_value = {
        "session_id": "sess-other",
        "accounts": [
            {
                "uid": "acc-other",
                "account_id": {
                    "iban": None,
                    "other": {"identification": "BBAN-12345", "scheme_name": "BBAN"},
                },
                "name": "Other Account",
                "currency": "EUR",
            }
        ],
        "aspsp": {"name": "TestBank"},
    }

    _, accounts = provider.authorize_session(
        code="code-4", bank_name="TestBank", country="ES"
    )

    assert len(accounts) == 1
    assert accounts[0].iban == "BBAN-12345"


def test_fetch_transactions_maps_response_to_domain() -> None:
    provider, mock_client = _make_provider()
    mock_client.get.return_value = {
        "transactions": [
            {
                "entry_reference": "tx-1",
                "booking_date": "2026-04-01",
                "transaction_amount": {"amount": "100.50", "currency": "EUR"},
                "credit_debit_indicator": "DBIT",
                "creditor": {"name": "Supermarket"},
                "remittance_information": ["Weekly shop"],
            }
        ]
    }

    transactions = provider.fetch_transactions(
        session_id="sess-xyz789", account_id="acc-1", bank_name="Imagin", country="ES"
    )

    assert len(transactions) == 1
    tx = transactions[0]
    assert tx.id == "tx-1"
    assert str(tx.amount) == "-100.50"
    assert tx.payee == "Supermarket"
    assert tx.notes == "Weekly shop"
    mock_client.get.assert_called_once_with(
        "/accounts/acc-1/transactions",
        params={"session_id": "sess-xyz789"},
    )


def test_fetch_transactions_payee_fallback() -> None:
    """Verify payee falls back to remittance info when names are absent."""
    provider, mock_client = _make_provider()
    mock_client.get.return_value = {
        "transactions": [
            {
                "entry_reference": "tx-2",
                "booking_date": "2026-04-01",
                "transaction_amount": {"amount": "30.00", "currency": "EUR"},
                "credit_debit_indicator": "DBIT",
                "remittance_information": ["Invoice 42"],
            }
        ]
    }

    transactions = provider.fetch_transactions(
        session_id="sess-xyz789", account_id="acc-1", bank_name="Imagin", country="ES"
    )

    assert transactions[0].payee == "Invoice 42"


def test_fetch_transactions_no_payee_fallback() -> None:
    """Verify payee defaults to 'Unknown Payee' when all name fields are absent."""
    provider, mock_client = _make_provider()
    mock_client.get.return_value = {
        "transactions": [
            {
                "entry_reference": "tx-3",
                "booking_date": "2026-04-01",
                "transaction_amount": {"amount": "5.00", "currency": "EUR"},
                "credit_debit_indicator": "CRDT",
            }
        ]
    }

    transactions = provider.fetch_transactions(
        session_id="sess-xyz789", account_id="acc-1", bank_name="Imagin", country="ES"
    )

    assert transactions[0].payee == "Unknown Payee"
