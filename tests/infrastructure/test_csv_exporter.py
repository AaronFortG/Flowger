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
            payee="Grocery Store",
        ),
        Transaction(
            id="tx2",
            account_id="acc1",
            date=date(2026, 3, 31),
            amount=Decimal("1000.00"),
            currency="EUR",
            payee="Salary",
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


def test_actual_csv_exporter_writes_header_only_for_empty_list(tmp_path: Path) -> None:
    output_file = tmp_path / "empty.csv"
    exporter = ActualCsvExporter()

    exporter.write_transactions([], str(output_file))

    content = output_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert len(lines) == 1
    assert lines[0] == "Date,Payee,Notes,Amount"


def test_actual_csv_exporter_custom_delimiter(tmp_path: Path) -> None:
    output_file = tmp_path / "semicolon.csv"
    transactions = [
        Transaction(
            id="tx1",
            account_id="acc1",
            date=date(2026, 4, 1),
            amount=Decimal("-50.00"),
            currency="EUR",
            payee="Grocery",
        ),
    ]
    exporter = ActualCsvExporter(delimiter=";")
    exporter.write_transactions(transactions, str(output_file))

    content = output_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0] == "Date;Payee;Notes;Amount"
    assert lines[1] == "2026-04-01;Grocery;;-50.00"


def test_actual_csv_exporter_safe_mode(tmp_path: Path) -> None:
    output_file = tmp_path / "safe.csv"
    transactions = [
        Transaction(
            id="tx1",
            account_id="acc1",
            date=date(2026, 4, 1),
            amount=Decimal("-50.00"),
            currency="EUR",
            payee='Store, "The" Store',
            notes="Note with 'quotes'",
        ),
    ]
    
    # Test safe mode (default)
    exporter_safe = ActualCsvExporter(safe=True)
    exporter_safe.write_transactions(transactions, str(output_file))
    lines_safe = output_file.read_text(encoding="utf-8").splitlines()
    # Quotes stripped, commas turned to spaces
    assert lines_safe[1] == "2026-04-01,Store  The Store,Note with quotes,-50.00"

    # Test unsafe mode
    output_unsafe = tmp_path / "unsafe.csv"
    exporter_unsafe = ActualCsvExporter(safe=False)
    exporter_unsafe.write_transactions(transactions, str(output_unsafe))
    lines_unsafe = output_unsafe.read_text(encoding="utf-8").splitlines()
    # CSV writer protects the comma by wrapping the field in double quotes
    assert lines_unsafe[1] == '2026-04-01,"Store, ""The"" Store",Note with \'quotes\',-50.00'
