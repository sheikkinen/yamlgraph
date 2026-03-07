#!/usr/bin/env bash
# FR-132: Copilot Co-authored-by trailer enforcement demo
# Demonstrates the commit-msg hook that rejects commits missing the trailer.
#
# Usage: ./examples/demos/copilot-trailer/demo.sh
set -euo pipefail

TRAILER='Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'

# The hook entry from .pre-commit-config.yaml
HOOK="bash -c 'grep -q \"Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\" \"\$1\" || { echo \"✗ Missing Co-authored-by: Copilot trailer\"; exit 1; }' _"

echo "═══════════════════════════════════════════════════"
echo "  FR-132: Copilot Trailer Enforcement Demo"
echo "═══════════════════════════════════════════════════"
echo ""

# --- Test 1: Missing trailer ---
echo "📝 Test 1: Commit without trailer"
MSG_FILE=$(mktemp)
echo "feat: FR-132 add feature" > "$MSG_FILE"
if eval "$HOOK" "$MSG_FILE" 2>&1; then
    echo "   ✅ Passed (unexpected)"
else
    echo "   ✗ Rejected — hook caught the missing trailer"
fi
rm -f "$MSG_FILE"
echo ""

# --- Test 2: With trailer ---
echo "📝 Test 2: Commit with trailer"
MSG_FILE=$(mktemp)
cat > "$MSG_FILE" << EOF
feat: FR-132 add trailer enforcement

$TRAILER
EOF
if eval "$HOOK" "$MSG_FILE" 2>&1; then
    echo "   ✅ Passed — trailer present, commit allowed"
else
    echo "   ✗ Rejected (unexpected)"
fi
rm -f "$MSG_FILE"
echo ""

# --- Test 3: Wrong email ---
echo "📝 Test 3: Commit with wrong Copilot email"
MSG_FILE=$(mktemp)
cat > "$MSG_FILE" << EOF
fix: correct bug

Co-authored-by: Copilot <wrong@email.com>
EOF
if eval "$HOOK" "$MSG_FILE" 2>&1; then
    echo "   ✅ Passed (unexpected)"
else
    echo "   ✗ Rejected — wrong email caught"
fi
rm -f "$MSG_FILE"
echo ""

echo "═══════════════════════════════════════════════════"
echo "  Setup: pre-commit install --hook-type commit-msg"
echo "═══════════════════════════════════════════════════"
