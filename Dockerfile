# ── Stage 1: builder ─────────────────────────────────────────────────────────
# Install dependencies into an isolated venv using uv.
# Using slim (Debian-based) to avoid native compilation issues with cryptography on Alpine.
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Install production deps only into /app/.venv
RUN uv sync --frozen --no-dev

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
# Lean final image: only the venv and source code.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the pre-built virtualenv from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY flowger/ ./flowger/
COPY pyproject.toml ./

# Put the venv on PATH so `flowger` CLI script resolves correctly
ENV PATH="/app/.venv/bin:$PATH"

# Default volume paths — override via env or docker-compose
ENV DATABASE_PATH=/data/flowger.db
ENV DEFAULT_EXPORT_FILE=/exports/transactions.csv

# Persistent data directories (db + exports)
VOLUME ["/data", "/exports", "/keys"]

# Safe default: printing help if container is started with no arguments
ENTRYPOINT ["flowger"]
CMD ["--help"]
