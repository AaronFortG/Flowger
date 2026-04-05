# ── Stage 1: builder ─────────────────────────────────────────────────────────
# Install dependencies into an isolated venv using uv.
# Using slim (Debian-based) to avoid native compilation issues with cryptography on Alpine.
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv from a pinned image version for reproducible builds
COPY --from=ghcr.io/astral-sh/uv:0.5.22 /uv /usr/local/bin/uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only first, without installing the local project
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
# Lean final image: only the venv and source code.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the pre-built virtualenv from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source, then install the project into /app/.venv
COPY flowger/ ./flowger/
COPY pyproject.toml ./
RUN /app/.venv/bin/uv sync --frozen --no-dev

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
