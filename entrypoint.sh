#!/bin/sh
set -e

# ── User / group configuration ─────────────────────────────────────────────
# Allow users to override UID/GID via environment variables (Docker convention).
RUN_UID="${PUID:-10001}"
RUN_GID="${PGID:-10001}"

# Resolve the runtime group.
# 1. If appgroup already exists and already has RUN_GID, use it as-is.
# 2. Else if another group already owns RUN_GID, reuse that group.
# 3. Else if appgroup exists with a different GID, update it to RUN_GID.
# 4. Else create appgroup with RUN_GID.
APPGROUP_GID=""
if getent group appgroup > /dev/null 2>&1; then
  APPGROUP_GID="$(getent group appgroup | cut -d: -f3)"
fi
EXISTING_GROUP="$(getent group "$RUN_GID" | cut -d: -f1 || true)"

if [ "$APPGROUP_GID" = "$RUN_GID" ]; then
  RUN_GROUP="appgroup"
elif [ -n "$EXISTING_GROUP" ]; then
  RUN_GROUP="$EXISTING_GROUP"
elif [ -n "$APPGROUP_GID" ]; then
  groupmod -g "$RUN_GID" appgroup
  RUN_GROUP="appgroup"
else
  groupadd -g "$RUN_GID" appgroup
  RUN_GROUP="appgroup"
fi

# Create or update the appuser with the desired UID/GID
if ! id appuser > /dev/null 2>&1; then
  useradd -u "$RUN_UID" -g "$RUN_GROUP" -M -s /bin/sh appuser
else
  # User exists — update UID/GID to match the requested values.
  # Fail fast if the update can't be applied (e.g., UID already taken by another user).
  if ! usermod -u "$RUN_UID" -g "$RUN_GROUP" appuser 2>/dev/null; then
    echo ""
    echo "  ERROR: Failed to update appuser to UID:GID $RUN_UID:$RUN_GID."
    echo ""
    echo "  This usually means the requested UID or GID is already in use."
    echo "  Choose different PUID/PGID values or remove the conflicting user/group."
    echo ""
    exit 1
  fi
fi

# Read back the actual UID/GID in case the image defaults were kept.
ACTUAL_RUN_UID="$(id -u appuser)"
ACTUAL_RUN_GID="$(id -g appuser)"

# ── Fix bind-mount permissions ──────────────────────────────────────────────
# Chown only the top-level directories and only when the owner already differs.
# Avoiding a recursive walk keeps startup fast even as /data and /exports grow.
for dir in /data /exports; do
  if [ -e "$dir" ] && [ "$(stat -c '%u:%g' "$dir" 2>/dev/null || true)" != "$ACTUAL_RUN_UID:$ACTUAL_RUN_GID" ]; then
    chown "$ACTUAL_RUN_UID:$ACTUAL_RUN_GID" "$dir" 2>/dev/null || true
  fi
done

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

if ! runuser -u appuser -- test -r "$KEY_PATH" 2>/dev/null; then
  echo ""
  echo "  ERROR: RSA private key exists at $KEY_PATH but is not readable by the runtime user."
  echo ""
  echo "  The file permissions may be too restrictive for appuser (UID $ACTUAL_RUN_UID)."
  echo "  Fix the permissions on your host (e.g., chmod 644 keys/private.pem),"
  echo "  or set PUID to match the file owner."
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
