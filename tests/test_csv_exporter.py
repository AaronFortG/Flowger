"""Tests for the CSV exporter."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from flowger.domain.models import Account, Transaction
from flowger.infrastructure.csv_exporter import export_to_csv

_ACCOUNT = Account(
    id="acc-test",
    name="Test Account",
    currency="EUR",
    provider="stub",
)

_TRANSACTIONS = [
    Transaction(
        id="tx-1",
        account_id="acc-test",
        date=date(2024, 1, 15),
        amount=Decimal("-42.50"),
        currency="EUR",
        description="Supermarket",
        reference="REF-001",
    ),
    Transaction(
        id="tx-2",
        account_id="acc-test",
        date=date(2024, 1, 20),
        amount=Decimal("2500.00"),
        currency="EUR",
        description="Salary",
    ),
]


class TestExportToCsv:
    def test_creates_file_in_output_dir(self, tmp_path: Path) -> None:
        filepath = export_to_csv(_TRANSACTIONS, _ACCOUNT, tmp_path)
        assert filepath.exists()
        assert filepath.parent == tmp_path

    def test_filename_uses_account_id(self, tmp_path: Path) -> None:
        filepath = export_to_csv(_TRANSACTIONS, _ACCOUNT, tmp_path)
        assert filepath.name == "acc-test.csv"

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        filepath = export_to_csv(_TRANSACTIONS, _ACCOUNT, nested)
        assert filepath.exists()

    def test_csv_has_correct_header(self, tmp_path: Path) -> None:
        filepath = export_to_csv(_TRANSACTIONS, _ACCOUNT, tmp_path)
        with filepath.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames == ["Date", "Payee", "Notes", "Amount"]

    def test_csv_row_count_matches_transactions(self, tmp_path: Path) -> None:
        filepath = export_to_csv(_TRANSACTIONS, _ACCOUNT, tmp_path)
        with filepath.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == len(_TRANSACTIONS)

    def test_csv_row_values_are_correct(self, tmp_path: Path) -> None:
        filepath = export_to_csv(_TRANSACTIONS, _ACCOUNT, tmp_path)
        with filepath.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))

        row = rows[0]
        assert row["Date"] == "2024-01-15"
        assert row["Payee"] == "Supermarket"
        assert row["Notes"] == "REF-001"
        assert row["Amount"] == "-42.50"

    def test_missing_reference_exported_as_empty_string(self, tmp_path: Path) -> None:
        filepath = export_to_csv(_TRANSACTIONS, _ACCOUNT, tmp_path)
        with filepath.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        # Second transaction has no reference
        assert rows[1]["Notes"] == ""

    def test_empty_transaction_list_creates_header_only(self, tmp_path: Path) -> None:
        filepath = export_to_csv([], _ACCOUNT, tmp_path)
        with filepath.open(encoding="utf-8") as fh:
            content = fh.read()
        assert "Date,Payee,Notes,Amount" in content
        rows = list(csv.DictReader(content.splitlines()))
        assert len(rows) == 0

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        # First export with 2 transactions
        export_to_csv(_TRANSACTIONS, _ACCOUNT, tmp_path)
        # Second export with only 1 transaction
        export_to_csv(_TRANSACTIONS[:1], _ACCOUNT, tmp_path)
        filepath = tmp_path / "acc-test.csv"
        with filepath.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 1
