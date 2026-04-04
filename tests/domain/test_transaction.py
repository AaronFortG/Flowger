from datetime import date
from decimal import Decimal

from flowger.domain.transaction import Transaction


def test_create_transaction_success() -> None:
    """Verify a Transaction can be instantiated with valid data."""
    txn = Transaction(
        id="txn_456",
        account_id="acc_123",
        amount=Decimal("-45.50"),
        currency="EUR",
        date=date(2026, 4, 4),
        description="Supermarket",
    )

    assert txn.id == "txn_456"
    assert txn.amount == Decimal("-45.50")
    assert txn.date == date(2026, 4, 4)
