FROM python:3.11-slim

WORKDIR /app

# Install dependencies first to leverage Docker layer caching.
COPY pyproject.toml .
# Stub package structure so pip can resolve the editable install.
RUN mkdir -p flowger && touch flowger/__init__.py
RUN pip install --no-cache-dir -e "."

# Copy the rest of the application.
COPY flowger/ flowger/

# Create directories for the database and exports.
RUN mkdir -p /data /exports

VOLUME ["/data", "/exports"]

ENV DATABASE_URL=sqlite:////data/flowger.db
ENV EXPORTS_DIR=/exports
ENV LOG_LEVEL=INFO
ENV PROVIDER=stub

ENTRYPOINT ["flowger"]
CMD ["--help"]
