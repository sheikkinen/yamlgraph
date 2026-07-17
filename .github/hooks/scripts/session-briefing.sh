#!/bin/sh
# FR-743: session-start briefing — fail-open at every seam.
# A briefing hook that blocks session start is worse than no briefing:
# any failure (missing venv, broken tap, dead python) yields silence
# and exit 0. Timeout guards the 5s hook budget.
REPO="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)" || exit 0
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)" || exit 0
cd "$REPO" 2>/dev/null || exit 0
if command -v timeout >/dev/null 2>&1; then
  timeout 5 "$PY" scripts/vscode/now.py --brief 2>/dev/null || true
else
  "$PY" scripts/vscode/now.py --brief 2>/dev/null || true
fi
exit 0
