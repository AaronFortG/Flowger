#!/bin/sh
set -e

# ── User / group configuration ─────────────────────────────────────────────
# Allow users to override UID/GID via environment variables (Docker convention).
RUN_UID="${PUID:-10001}"
RUN_GID="${PGID:-10001}"

# Create the group if it doesn't already exist
if ! getent group appgroup > /dev/null 2>&1; then
  groupadd -g "$RUN_GID" appgroup 2>/dev/null || true
fi

# Create or update the appuser with the desired UID/GID
if ! id appuser > /dev/null 2>&1; then
  useradd -u "$RUN_UID" -g appgroup -M -s /bin/sh appuser
else
  # User exists — update UID/GID if they differ from the image defaults
  usermod -u "$RUN_UID" -g appgroup appuser 2>/dev/null || true
fi

# ── Fix bind-mount permissions ──────────────────────────────────────────────
# Host bind mounts override image ownership. Ensure the runtime user owns
# /data and /exports so it can write the SQLite DB and exported CSVs.
chown -R "$RUN_UID:$RUN_GID" /data /exports 2>/dev/null || true

# ── Pre-flight checks ─────────────────────────────────────────────────────
# Default key path can be overridden via ENABLEBANKING_KEY_PATH env var.
KEY_PATH="${ENABLEBANKING_KEY_PATH:-/keys/private.pem}"

if [ ! -f "$KEY_PATH" ]; then
  echo ""
  echo "  ERROR: RSA private key not found at: $KEY_PATH"
  echo ""
  echo "  Flowger needs your Enable Banking RSA key to authenticate with your bank."
  echo ""
  echo "  How to fix this:"
  echo ""
  echo "  1. Download your RSA key from your Enable Banking application settings."
  echo "  2. Save it to 'keys/private.pem' in this project directory (or set"
  echo "     ENABLEBANKING_KEY_PATH to a different path in docker-compose.yml)."
  echo "  3. Restart the container:"
  echo ""
  echo "       docker compose up -d"
  echo ""
  exit 1
fi

if [ -z "$ENABLEBANKING_APP_ID" ]; then
  echo ""
  echo "  ERROR: ENABLEBANKING_APP_ID is not set."
  echo ""
  echo "  Set it in your docker-compose.yml environment block:"
  echo ""
  echo "    - ENABLEBANKING_APP_ID=your_app_id_here"
  echo ""
  exit 1
fi

# ── Drop privileges and hand off to the real command ────────────────────────
# runuser is part of util-linux (Essential: yes on Debian).
exec runuser -u appuser -- "$@"
