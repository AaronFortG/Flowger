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

## Quick Start — Docker (Recommended)

Flowger runs as a Docker daemon. You only need to set a few environment variables and run `docker compose up -d`. On first start, the container guides you through bank setup interactively, then runs as a daemon syncing on your schedule.

### 1. Clone the repository

```bash
git clone https://github.com/aaronfortg/flowger.git
cd flowger
```

### 2. Place your RSA key

Put your Enable Banking RSA private key at `keys/private.pem`:

```bash
mkdir -p keys
cp /path/to/your/private.pem keys/private.pem
```

### 3. Edit `docker-compose.yml` environment variables

Open `docker-compose.yml` and update the `environment:` block for your service:

```yaml
environment:
  # Required: Enable Banking credentials
  - ENABLEBANKING_APP_ID=your_app_id_here

  # Required: Bank scope for this container
  - BANK=Imagin
  - COUNTRY=ES

  # Optional: Sync schedule (default: every 6 hours)
  - SYNC_CRON=0 */6 * * *

  # Optional: Storage paths (defaults shown)
  - DATABASE_PATH=/data/flowger.db

  # Optional: File permissions — match your host user so exported files
  # are owned by you. Run `id -u` / `id -g` on your host to find the values.
  # - PUID=1000
  # - PGID=1000
```

The RSA key path defaults to `/keys/private.pem` inside the container, which matches the default volume mount (`./keys/private.pem:/keys/private.pem:ro`). You only need to set `ENABLEBANKING_KEY_PATH` if you use a different path.

> **Tip:** To add a second bank, duplicate the service block with a different `BANK`, `COUNTRY`, and `SYNC_CRON`. All services share the same `db` volume so transactions from all banks land in one database.

### 4. Start the daemon

```bash
docker compose up -d
```

On **first run**, the container detects no accounts and prints an authorization URL. View it with:

```bash
docker compose logs -f flowger-imagin
```

Open the URL, authenticate with your bank, then copy the `code` from the redirected URL (`?code=...`). Complete setup with:

```bash
docker compose exec --user appuser flowger-imagin flowger authorize --code <CODE>
```

The daemon detects the account automatically, runs the initial sync, exports CSV files to `./exports/`, and starts the scheduled loop.

### 5. Useful commands

```bash
docker compose exec --user appuser flowger-imagin flowger accounts               # List accounts
docker compose exec --user appuser flowger-imagin flowger sync                    # Manual sync
docker compose exec --user appuser flowger-imagin flowger export --account-id <ID>  # Manual export
```

> **Note:** Pass `--user appuser` to `docker compose exec` so that exported files on the host bind mount are owned by `appuser` (UID 10001) rather than root. Omit it only if you intentionally want root-owned output.

---

## Local Setup (Python)

Prefer to run Flowger directly with Python? Follow these steps.

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

# Optional defaults (to avoid passing --bank and --country on every command)
# DEFAULT_BANK=
# DEFAULT_COUNTRY=

# Optional
# DATABASE_PATH=flowger.db
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

## Full Usage Flow (Local Python)

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

https://auth.enablebanking.com/auth/...

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

## Running with Docker

Pre-built images are published to both Docker Hub and GitHub Container Registry on every release:

```bash
docker pull aaronfort/flowger:latest
# or
docker pull ghcr.io/aaronfortg/flowger:latest
```

### Daemon via docker-compose (Recommended)

See the [Quick Start](#quick-start--docker-recommended) section above for the full setup.

All services share the same `db` volume, so transactions from all banks land in one database. For daemon auto-export, `DEFAULT_EXPORT_FILE` determines the export directory — Flowger writes one CSV per account using the filename `<bank>-<country>-<account_id>.csv` inside that directory. To keep exports isolated per bank when services share `/exports`, point each service's `DEFAULT_EXPORT_FILE` at a bank-specific subdirectory (for example, `/exports/imagin/export.csv` and `/exports/santander/export.csv`).

### One-shot commands

Run any CLI command and exit:

```bash
docker compose exec --user appuser flowger-imagin flowger accounts
```

---

## Environment Variables

| Variable | Docker / daemon | Local Python CLI | Description |
|---|---|---|---|
| `ENABLEBANKING_APP_ID` | Required | Required | Your Enable Banking app ID |
| `ENABLEBANKING_KEY_PATH` | No (default: `/keys/private.pem`) | **Required** | Path to RSA private key (PEM). Set in `.env` for local runs; the Dockerfile sets the container default. |
| `BANK` | **Required** | No | Bank name. Required when running the daemon via Docker. For local CLI, pass `--bank` or use `DEFAULT_BANK`. |
| `COUNTRY` | **Required** | No | Country code. Required when running the daemon via Docker. For local CLI, pass `--country` or use `DEFAULT_COUNTRY`. |
| `SYNC_CRON` | No | No | Cron schedule for daemon sync (default: `0 */6 * * *`) |
| `DATABASE_PATH` | No | No | SQLite DB path (default: `/data/flowger.db` in Docker) |
| `PUID` | No | No | Host user UID for file ownership (default: `10001`) |
| `PGID` | No | No | Host group GID for file ownership (default: `10001`) |
| `DEFAULT_BANK` | No | No | Fallback bank for local Python CLI (`.env` only) |
| `DEFAULT_COUNTRY` | No | No | Fallback country for local Python CLI (`.env` only) |
| `DEFAULT_REDIRECT_URL` | No | No | OAuth redirect URL |
| `DEFAULT_EXPORT_FILE` | No | No | Default CSV export path (directory used for daemon auto-export) |

---

## License

MIT
