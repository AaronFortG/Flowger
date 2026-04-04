import pytest
from pydantic import ValidationError

from flowger.domain.account import Account


def test_create_account_success() -> None:
    """Verify an Account can be instantiated with valid data."""
    account = Account(id="acc_123", iban="ES1234567890", name="Main Checking", currency="EUR")

    assert account.id == "acc_123"
    assert account.iban == "ES1234567890"


def test_create_account_invalid_data() -> None:
    """Verify validation fails if required fields are missing."""
    with pytest.raises(ValidationError):
        Account(  # type: ignore[call-arg]
            id="acc_123",
            name="Main Checking",
            currency="EUR",
        )
