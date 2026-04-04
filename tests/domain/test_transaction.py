import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from flowger.domain.transaction import Transaction


def test_create_transaction_success() -> None:
    """Verify a Transaction can be instantiated with valid data."""
    txn = Transaction(
        id="txn_456",
        account_id="acc_123",
        amount=Decimal("-45.50"),
        currency="EUR",
        date=date(2026, 4, 4),
        payee="Supermarket",
        notes="Note 1",
    )

    assert txn.id == "txn_456"
    assert txn.amount == Decimal("-45.50")
    assert txn.date == date(2026, 4, 4)
    assert txn.notes == "Note 1"


def test_create_transaction_invalid_data() -> None:
    """Verify validation fails when required fields are missing."""
    with pytest.raises(ValidationError):
        Transaction(  # type: ignore[call-arg]
            id="txn_456",
            account_id="acc_123",
            currency="EUR",
            description="Missing date and amount",
        )
