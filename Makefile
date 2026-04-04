.DEFAULT_GOAL := help

# ─── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:  ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ─── Setup ────────────────────────────────────────────────────────────────────

.PHONY: install
install:  ## Install all dependencies (including dev)
	uv sync --all-groups

.PHONY: env
env:  ## Copy .env.example to .env (skip if already exists)
	@test -f .env && echo ".env already exists, skipping." || (cp .env.example .env && echo "Created .env from .env.example")

# ─── Quality ──────────────────────────────────────────────────────────────────

.PHONY: test
test:  ## Run the full test suite
	uv run pytest

.PHONY: test-v
test-v:  ## Run tests with verbose output
	uv run pytest -v

.PHONY: lint
lint:  ## Check code style with ruff
	uv run ruff check .

.PHONY: format
format:  ## Auto-format code with ruff
	uv run ruff format .

.PHONY: typecheck
typecheck:  ## Run mypy type checker
	uv run mypy flowger/

.PHONY: check
check: lint typecheck test  ## Run lint + typecheck + tests

# ─── Flowger CLI shortcuts ───────────────────────────────────────────────────

.PHONY: config
config:  ## Verify application configuration
	uv run flowger config

.PHONY: login
login:  ## Start the bank authorization flow (generates URL to open in browser)
	uv run flowger login

.PHONY: sync
sync:  ## Sync bank accounts from provider to local DB
	uv run flowger sync

.PHONY: sync-transactions
sync-transactions:  ## Sync transactions for all local accounts
	uv run flowger sync-transactions

.PHONY: accounts
accounts:  ## List all synced accounts and their IDs
	uv run flowger accounts

.PHONY: db
db:  ## Open an interactive SQLite shell on flowger.db
	sqlite3 flowger.db

.PHONY: db-accounts
db-accounts:  ## Print accounts table directly from SQLite
	sqlite3 -column -header flowger.db "SELECT id, iban, name, currency FROM accounts;"

.PHONY: db-transactions
db-transactions:  ## Print last 20 transactions directly from SQLite
	sqlite3 -column -header flowger.db "SELECT account_id, date, description, amount, currency FROM transactions ORDER BY date DESC LIMIT 20;"

# ─── Utilities ────────────────────────────────────────────────────────────────

.PHONY: clean-db
clean-db:  ## Delete the local SQLite database (irreversible)
	@read -p "Delete flowger.db? [y/N] " ans; [ "$$ans" = "y" ] && rm -f flowger.db && echo "Deleted." || echo "Aborted."
