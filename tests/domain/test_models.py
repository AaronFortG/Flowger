from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError

from flowger.domain.models import Account, Transaction


def test_create_account_success():
    """Verify an Account can be instantiated with valid data."""
    account = Account(
        id="acc_123",
        iban="ES1234567890",
        name="Main Checking",
        currency="EUR"
    )
    
    assert account.id == "acc_123"
    assert account.iban == "ES1234567890"


def test_create_account_invalid_data():
    """Verify validation fails if required fields are missing."""
    with pytest.raises(ValidationError):
        Account(
            id="acc_123",
            name="Main Checking",
            currency="EUR"
            # Missing iban
        )


def test_create_transaction_success():
    """Verify a Transaction can be instantiated with valid data."""
    txn = Transaction(
        id="txn_456",
        account_id="acc_123",
        amount=Decimal("-45.50"),
        date=date(2026, 4, 4),
        description="Supermarket"
    )
    
    assert txn.id == "txn_456"
    assert txn.amount == Decimal("-45.50")
    assert txn.date == date(2026, 4, 4)
