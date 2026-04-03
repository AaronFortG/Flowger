# Flowger

**Sync bank transactions into your ledger.**

Flowger fetches transactions from a banking provider, persists them locally in
SQLite, and exports them as CSV files compatible with
[Actual Budget](https://actualbudget.org/).

---

## Features

- Discover and store multiple bank accounts
- Incremental sync (only fetches new transactions since the last run)
- Idempotent upsert (no duplicate transactions)
- Per-account CSV export (Actual Budget-compatible format)
- Pluggable banking provider (stub for local dev, Enable Banking for production)
- Configuration via environment variables / `.env` file
- Runs easily with Docker and docker compose

---

## Quick start (local)

```bash
# Install
pip install -e "."

# Copy and edit the example config
cp .env.example .env

# Discover accounts from the stub provider
flowger discover

# Sync transactions (last 30 days by default)
flowger sync-all

# Export transactions to CSV
flowger export-all
```

Exported CSV files will be written to `./exports/` (one file per account).

---

## Quick start (Docker)

```bash
# Build and run
docker compose run flowger discover
docker compose run flowger sync-all
docker compose run flowger export-all
```

The SQLite database is persisted in `./data/` and CSV exports land in
`./exports/` on the host.

---

## CLI reference

```
flowger --help

Commands:
  accounts     List all accounts stored locally
  discover     Discover accounts from the configured banking provider
  sync         Sync transactions for one account
  sync-all     Sync transactions for all stored accounts
  export       Export transactions for one account to CSV
  export-all   Export transactions for all accounts to CSV
```

### Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./flowger.db` | SQLAlchemy database URL |
| `EXPORTS_DIR` | `./exports` | Directory for exported CSV files |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `PROVIDER` | `stub` | Banking provider (`stub` or `enable_banking`) |
| `ENABLE_BANKING_BASE_URL` | `https://api.enablebanking.com` | Enable Banking API base URL |
| `ENABLE_BANKING_API_KEY` | *(empty)* | Enable Banking API key |

---

## CSV format

Exported files are named `<account-id>.csv` and use the following columns,
which are compatible with Actual Budget's CSV import:

| Column | Description |
|---|---|
| `Date` | ISO 8601 date (YYYY-MM-DD) |
| `Payee` | Transaction description / merchant name |
| `Notes` | Optional reference or memo |
| `Amount` | Decimal value (negative = expense, positive = income) |

---

## Architecture

```
flowger/
├── domain/          # Plain dataclasses + port interfaces (no external deps)
│   ├── models.py    # Account, Transaction
│   └── ports.py     # BankingProvider, TransactionRepository (ABCs)
├── application/     # Use cases (sync, export)
│   └── use_cases.py
├── infrastructure/  # SQLite, CSV, HTTP adapters
│   ├── database.py        # SQLAlchemy engine factory
│   ├── db_models.py       # SQLModel ORM table definitions
│   ├── repositories.py    # SQLite implementation of TransactionRepository
│   ├── csv_exporter.py    # CSV writer
│   ├── stub_provider.py   # Stub provider for local dev / testing
│   └── enable_banking.py  # Enable Banking HTTP client (skeleton)
├── config.py        # Pydantic Settings
└── cli.py           # Typer CLI (wiring layer)
```

The domain layer has **no external dependencies** – it is pure Python.
Infrastructure details (database, HTTP, CSV) are isolated in their own layer.
The CLI is the only place where all layers are wired together.

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Lint
ruff check flowger/ tests/

# Type check
mypy flowger/

# Test
pytest tests/ -v --cov=flowger

# Security scan
bandit -r flowger/ -ll
pip-audit
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes and add tests
4. Ensure `ruff`, `mypy`, and `pytest` all pass
5. Open a pull request

---

## Roadmap

- [ ] Enable Banking API integration (PSU consent flow)
- [ ] Per-account sync configuration (custom date ranges, field mapping)
- [ ] Scheduled sync (cron / systemd timer)
- [ ] PostgreSQL support
- [ ] Web UI

---

## License

[MIT](LICENSE)
