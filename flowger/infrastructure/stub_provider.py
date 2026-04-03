"""Stub banking provider for local development and testing.

Generates deterministic fake transactions so the full sync → export workflow
can be exercised without real API credentials.
"""

from datetime import date, timedelta
from decimal import Decimal

from flowger.domain.models import Account, Transaction
from flowger.domain.ports import BankingProvider

_STUB_ACCOUNTS = [
    Account(
        id="acc-stub-001",
        name="Main Checking (stub)",
        currency="EUR",
        provider="stub",
        iban="FR7630006000011234567890189",
    ),
    Account(
        id="acc-stub-002",
        name="Savings (stub)",
        currency="EUR",
        provider="stub",
        iban="FR7630006000019876543210189",
    ),
]

# One synthetic transaction per day, alternating credit / debit.
_STUB_TRANSACTIONS = [
    {"description": "Supermarket", "amount": Decimal("-42.50")},
    {"description": "Salary", "amount": Decimal("2500.00")},
    {"description": "Electricity bill", "amount": Decimal("-85.20")},
    {"description": "Restaurant", "amount": Decimal("-23.00")},
    {"description": "Online transfer", "amount": Decimal("-150.00")},
    {"description": "ATM withdrawal", "amount": Decimal("-60.00")},
    {"description": "Freelance payment", "amount": Decimal("800.00")},
]


class StubBankingProvider(BankingProvider):
    """Returns hard-coded accounts and generates one transaction per day."""

    def get_accounts(self) -> list[Account]:
        return list(_STUB_ACCOUNTS)

    def get_transactions(
        self, account_id: str, from_date: date, to_date: date
    ) -> list[Transaction]:
        transactions: list[Transaction] = []
        current = from_date
        index = 0
        while current <= to_date:
            template = _STUB_TRANSACTIONS[index % len(_STUB_TRANSACTIONS)]
            transactions.append(
                Transaction(
                    # Deterministic ID: same call always produces the same ID.
                    id=f"tx-{account_id}-{current.isoformat()}",
                    account_id=account_id,
                    date=current,
                    amount=template["amount"],  # type: ignore[arg-type]
                    currency="EUR",
                    description=template["description"],  # type: ignore[arg-type]
                )
            )
            current += timedelta(days=1)
            index += 1
        return transactions
