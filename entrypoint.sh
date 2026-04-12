#!/bin/sh
set -e

# ── Fix bind-mount permissions ──────────────────────────────────────────────
# Host bind mounts override image ownership. Ensure appuser (UID 10001) can
# write to /data and /exports before handing off.
chown -R 10001:10001 /data /exports 2>/dev/null || true

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

# ── Drop to appuser and hand off to the real command ────────────────────────
exec su-exec 10001:10001 "$@"
