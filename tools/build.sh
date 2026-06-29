#!/usr/bin/env bash
# Reproducible build for MementoBloom
# Usage: ./build.sh [--with-dev]
set -euo pipefail

REQUIREMENTS_RUNTIME="requirements.txt"
REQUIREMENTS_LOCK="requirements-lock.txt"
REQUIREMENTS_DEV="requirements-dev.txt"

echo "=== MementoBloom Reproducible Build ==="

# Install runtime deps from lockfile (pinned)
if [[ -f "$REQUIREMENTS_LOCK" ]]; then
  echo "[1/3] Installing runtime dependencies from lockfile..."
  pip install --no-cache-dir -r "$REQUIREMENTS_LOCK"
else
  echo "[1/3] No lockfile found, installing from requirements.txt..."
  pip install --no-cache-dir -r "$REQUIREMENTS_RUNTIME"
fi

# Optionally install dev dependencies
if [[ "${1:-}" == "--with-dev" ]] && [[ -f "$REQUIREMENTS_DEV" ]]; then
  echo "[2/3] Installing dev dependencies..."
  pip install --no-cache-dir -r "$REQUIREMENTS_DEV"
else
  echo "[2/3] Skipping dev dependencies (use --with-dev to include)"
fi

# Verify installation
echo "[3/3] Verifying installation..."
python3 -c "import sys; print('Python', sys.version)"
python3 -c "import core.paths; import tools.session_start; print('Core modules OK')"

echo "=== Build complete ==="
