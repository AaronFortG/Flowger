# ── Stage 1: builder ─────────────────────────────────────────────────────────
# Install dependencies into an isolated venv using uv.
# Using slim (Debian-based) to avoid native compilation issues with cryptography on Alpine.
FROM python:3.12-slim AS builder

# Install uv from a pinned image version for reproducible builds
COPY --from=ghcr.io/astral-sh/uv:0.5.22 /uv /usr/local/bin/uv

WORKDIR /app

# Enable bytecode compilation for slightly faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Install only production dependencies, without the local project yet
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source and install the project non-editably
COPY flowger/ ./flowger/
COPY pyproject.toml uv-lock README.md ./
RUN uv sync --frozen --no-dev --no-editable

# ─── Stage 2: runtime ─────────────────────────────────────────────────────────
# Lean final image: only the venv and source code.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the pre-built virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy source and metadata (useful for debugging, though not strictly needed for runtime)
COPY flowger/ ./flowger/
COPY pyproject.toml ./

# Create a non-root user for security (UID 10001)
RUN useradd --create-home --uid 10001 appuser && \
    mkdir -p /data /exports /keys && \
    chown -R appuser:appuser /app /data /exports /keys

USER appuser

# Put the venv on PATH so `flowger` CLI script resolves correctly
ENV PATH="/app/.venv/bin:$PATH"

# Default environment variables for container use
ENV DATABASE_PATH=/data/flowger.db
ENV DEFAULT_EXPORT_FILE=/exports/transactions.csv
ENV PYTHONUNBUFFERED=1

# Persistence volumes
VOLUME ["/data", "/exports", "/keys"]

ENTRYPOINT ["flowger"]
CMD ["--help"]
