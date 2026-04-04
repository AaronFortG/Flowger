from datetime import date
from decimal import Decimal
from pathlib import Path

from flowger.domain.transaction import Transaction
from flowger.infrastructure.exporters.csv import ActualCsvExporter


def test_actual_csv_exporter_writes_correct_format(tmp_path: Path) -> None:
    # 1. Arrange
    output_file = tmp_path / "test.csv"
    transactions = [
        Transaction(
            id="tx1",
            account_id="acc1",
            date=date(2026, 4, 1),
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Grocery Store",
        ),
        Transaction(
            id="tx2",
            account_id="acc1",
            date=date(2026, 3, 31),
            amount=Decimal("1000.00"),
            currency="EUR",
            description="Salary",
        ),
    ]
    exporter = ActualCsvExporter()

    # 2. Act
    exporter.write_transactions(transactions, str(output_file))

    # 3. Assert
    content = output_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    assert lines[0] == "Date,Payee,Notes,Amount"
    # tx2 should come first because it's earlier (2026-03-31)
    assert lines[1] == "2026-03-31,Salary,,1000.00"
    assert lines[2] == "2026-04-01,Grocery Store,,-50.00"
