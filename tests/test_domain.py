"""Tests for domain models.

Domain models are plain dataclasses – tests verify construction and defaults.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from flowger.domain.models import Account, Transaction


class TestAccount:
    def test_required_fields(self) -> None:
        acc = Account(id="acc-1", name="Checking", currency="EUR", provider="stub")
        assert acc.id == "acc-1"
        assert acc.name == "Checking"
        assert acc.currency == "EUR"
        assert acc.provider == "stub"
        assert acc.iban is None  # optional

    def test_with_iban(self) -> None:
        acc = Account(
            id="acc-2",
            name="Savings",
            currency="EUR",
            provider="stub",
            iban="FR7630006000011234567890189",
        )
        assert acc.iban == "FR7630006000011234567890189"


class TestTransaction:
    def test_required_fields(self) -> None:
        tx = Transaction(
            id="tx-1",
            account_id="acc-1",
            date=date(2024, 1, 15),
            amount=Decimal("-42.50"),
            currency="EUR",
            description="Supermarket",
        )
        assert tx.id == "tx-1"
        assert tx.account_id == "acc-1"
        assert tx.date == date(2024, 1, 15)
        assert tx.amount == Decimal("-42.50")
        assert tx.currency == "EUR"
        assert tx.description == "Supermarket"
        assert tx.reference is None  # optional

    def test_created_at_defaults_to_now(self) -> None:
        before = datetime.now(UTC)
        tx = Transaction(
            id="tx-2",
            account_id="acc-1",
            date=date(2024, 1, 15),
            amount=Decimal("100.00"),
            currency="EUR",
            description="Income",
        )
        after = datetime.now(UTC)
        assert before <= tx.created_at <= after

    def test_with_reference(self) -> None:
        tx = Transaction(
            id="tx-3",
            account_id="acc-1",
            date=date(2024, 1, 15),
            amount=Decimal("-15.00"),
            currency="EUR",
            description="Pharmacy",
            reference="REF-001",
        )
        assert tx.reference == "REF-001"

    def test_positive_amount_for_income(self) -> None:
        tx = Transaction(
            id="tx-4",
            account_id="acc-1",
            date=date(2024, 1, 1),
            amount=Decimal("2500.00"),
            currency="EUR",
            description="Salary",
        )
        assert tx.amount > Decimal("0")
