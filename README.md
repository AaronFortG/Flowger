# Flowger

> Sync bank transactions locally and export them to CSV for [Actual Budget](https://actualbudget.org/).

Flowger is an open-source command-line tool that authenticates with a bank via [Enable Banking](https://enablebanking.com/), pulls your transactions, stores them in a local SQLite database, and exports a CSV file you can import directly into Actual Budget.

It is also a learning project — intentionally built with a clean layered architecture (domain → application → ports → infrastructure → entrypoints) so it is easy to read, extend, and adapt.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | ≥ 3.10 |
| [uv](https://docs.astral.sh/uv/) | any recent |
| Enable Banking account | [enablebanking.com](https://enablebanking.com/) |
| RSA private key (PEM) | generated for your Enable Banking app |

> **Note:** `uv` is the recommended package and environment manager. All commands below use it.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/flowger.git
cd flowger
```

### 2. Install dependencies

```bash
uv sync --all-groups
```

### 3. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
ENABLEBANKING_APP_ID=your_app_id
ENABLEBANKING_ENVIRONMENT=SANDBOX       # or PRODUCTION
ENABLEBANKING_KEY_PATH=/path/to/private.key

# Optional — these have defaults
DATABASE_PATH=flowger.db
DEFAULT_BANK=Imagin
DEFAULT_COUNTRY=ES
DEFAULT_REDIRECT_URL=http://localhost:8000/callback
DEFAULT_EXPORT_FILE=transactions.csv
```

### 4. Verify configuration

```bash
uv run flowger config
```

Expected output:
```
Configuration is valid.
Environment: SANDBOX
```

---

## Full Usage Flow

Flowger works in five steps. Run them in order the first time.

### Step 1 — Generate an authorization URL

```bash
uv run flowger login
# or with explicit options:
uv run flowger login --bank Imagin --country ES
```

Expected output:
```
Requesting authorization for Imagin (ES)...

Open the following URL in your browser to authenticate:

https://api.enablebanking.com/auth/...

After authenticating, run:
  flowger authorize --code <CODE> --bank <BANK> --country <COUNTRY>
```

Open the printed URL in your browser and complete the bank login. You will be redirected to `http://localhost:8000/callback?code=<CODE>&...`. Copy the `code` value from the URL.

### Step 2 — Exchange the code for a session

```bash
uv run flowger authorize --code <CODE>
# or:
uv run flowger authorize --code <CODE> --bank Imagin --country ES
```

Expected output:
```
Authorizing session for Imagin (ES)...
Session authorized and saved. Session ID: sess-abc123...
```

The session is stored in the local SQLite database and reused for all subsequent commands.

### Step 3 — Sync accounts

```bash
uv run flowger sync
```

Expected output:
```
Fetching accounts for Imagin (ES)...
Account sync complete.
```

Your bank accounts are now stored locally.

### Step 4 — Sync transactions

```bash
uv run flowger sync-transactions
```

Expected output:
```
Syncing transactions for all accounts in Imagin (ES)...
Transaction sync complete.
```

Transactions are fetched for every synced account and stored in SQLite. Running this again is safe — duplicates are skipped via upsert.

### Step 5 — Export to CSV

```bash
uv run flowger export --account-id <ACCOUNT_UID>
# or with a custom output path:
uv run flowger export --account-id <ACCOUNT_UID> --output myaccount.csv
```

Expected output:
```
Exporting transactions for account acc-xyz to transactions.csv...
Export complete. File saved to transactions.csv.
```

The CSV is formatted for direct import into **Actual Budget** (`Date, Payee, Notes, Amount`).

---

## Development

### Install dev dependencies

```bash
uv sync --all-groups
```

### Run tests

```bash
uv run pytest
```

### Lint

```bash
uv run ruff check .
```

### Format

```bash
uv run ruff format .
```

### Type check

```bash
uv run mypy flowger/
```

---

## Project Structure

```
flowger/
├── domain/              # Pure domain models and exceptions (no dependencies)
├── application/         # Use cases and port protocols (no infrastructure)
├── infrastructure/      # SQLite, Enable Banking adapter, CSV exporter, config
└── entrypoints/cli/     # Typer CLI — parses input, calls use cases, prints output
tests/                   # Mirrors source structure
docs/spec.md             # Full product specification
.env.example             # Configuration template
```

---

## CSV Output Format

The exported CSV is compatible with Actual Budget's transaction import:

```csv
Date,Payee,Notes,Amount
2026-03-31,Salary,,1000.00
2026-04-01,Grocery Store,,-50.00
```

Transactions are sorted oldest-first. Amounts follow the sign convention: **positive = credit, negative = debit**.

---

## License

MIT
