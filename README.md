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
ENABLEBANKING_KEY_PATH=/path/to/private.key

# Optional (commented = default value applies)
# DATABASE_PATH=flowger.db
# DEFAULT_BANK=Imagin
# DEFAULT_COUNTRY=ES
# DEFAULT_REDIRECT_URL=https://enablebanking.com/ais/
# DEFAULT_EXPORT_FILE=transactions.csv
```

### 4. Verify configuration

```bash
uv run flowger config
```

Expected output:
```
Configuration is valid.
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

Open the printed URL in your browser and complete the bank login. You will be redirected to `https://enablebanking.com/ais/?code=<CODE>&state=...`. Copy the `code` value from the browser address bar.

### Step 2 — Exchange the code for a session

```bash
uv run flowger authorize --code <CODE>
# or:
uv run flowger authorize --code <CODE> --bank Imagin --country ES
```

Expected output:
```
Authorizing session for Imagin (ES)...
Session authorized and 1 accounts saved. Session ID: sess-abc123...
```

The session and associated accounts are stored in the local SQLite database and reused for all subsequent commands.

### Step 3 — List accounts

You can view the accounts that were authorized and stored locally to find your Account ID (needed for exporting):

```bash
uv run flowger accounts
```

Expected output:
```
ID                                       IBAN                       Name                 Currency
------------------------------------------------------------------------------------------------
acc-xyz                                  ES00000000001              Checking Account      EUR
```

### Step 4 — Sync transactions

```bash
uv run flowger sync
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
# or with a custom output path and separator options:
uv run flowger export --account-id <ACCOUNT_UID> --output myaccount.csv --delimiter ";" --no-safe
```

Available CLI Flags:
* `--account-id`: The UID of the account
* `--output`: Path to the CSV (defaults to `transactions.csv`)
* `--delimiter`: Changes the CSV column separator (defaults to `,`)
* `--safe` / `--no-safe`: Toggles string sterilization (defaults to `--safe`). 
  
**About `safe` mode and Quotes:**
Actual Budget requires precise CSV imports and often crashes when double-quotes are encountered. By default, `csv.writer` automatically wraps fields in double-quotes (`""`) when a field contains characters that require quoting, such as the current `--delimiter`. To protect brittle importers, Flowger defaults to `--safe`, which strips quote characters and sanitizes strings that contain the active delimiter (for example, converting nested commas into spaces if `,` is the delimiter) before CSV writing to reduce the likelihood of generated quotes. Some content, such as embedded newlines, may still cause `csv.writer` to quote a field. Pass `--no-safe` if you want less-sanitized output written as-is apart from normal CSV escaping rules.

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
