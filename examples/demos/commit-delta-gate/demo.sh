#!/usr/bin/env bash
# FR-131: Commit-delta gate demo
# Demonstrates the Inquisitor's gate logic that prevents audit-as-ritual.
#
# The gate extracts the last audit SHA from docs/diary.md, counts feat/fix
# commits since that SHA, and blocks if none are found.
#
# Usage: ./examples/demos/commit-delta-gate/demo.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "═══════════════════════════════════════════════════"
echo "  FR-131: Inquisitor Commit-Delta Gate Demo"
echo "═══════════════════════════════════════════════════"
echo ""

# --- 1. SHA extraction ---
echo "📖 Step 1: Extract last audit SHA from docs/diary.md"
LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\.\.`([a-f0-9]{7,})`.*/\2/p' docs/diary.md 2>/dev/null | head -1)
if [[ -z "$LAST_SHA" ]]; then
    echo "   No audit SHA found — gate degrades gracefully (PASS)"
else
    echo "   Last audit endpoint: $LAST_SHA"
fi
echo ""

# --- 2. Actionable commit count ---
echo "🔍 Step 2: Count feat/fix commits since $LAST_SHA"
if [[ -n "$LAST_SHA" ]] && git rev-parse --verify "$LAST_SHA^{commit}" >/dev/null 2>&1; then
    TOTAL=$(git log --oneline "$LAST_SHA"..HEAD | wc -l | tr -d ' ')
    ACTIONABLE=$(git log --oneline "$LAST_SHA"..HEAD | grep -cE '^[a-f0-9]+ (feat|fix)' || true)
    echo "   Total commits since last audit: $TOTAL"
    echo "   Actionable (feat/fix) commits:  $ACTIONABLE"
else
    echo "   SHA unresolvable — gate degrades gracefully (PASS)"
    ACTIONABLE=1
fi
echo ""

# --- 3. Gate decision ---
echo "🚦 Step 3: Gate decision"
if [[ "$ACTIONABLE" -eq 0 ]]; then
    echo "   ⏭️  BLOCKED — No actionable commits. Audit would repeat findings."
    echo "   Use: .chaplain/inquisitor.sh --force    (to override)"
else
    echo "   ✅ PASS — $ACTIONABLE actionable commit(s) found. Audit would be productive."
fi
echo ""

# --- 4. Flag composition ---
echo "🏁 Step 4: Flag composition"
echo "   .chaplain/inquisitor.sh              → gate applies"
echo "   .chaplain/inquisitor.sh --force      → gate bypassed"
echo "   .chaplain/inquisitor.sh --propose    → gate applies, then propose"
echo "   .chaplain/inquisitor.sh --force --propose → bypass + propose"
echo ""
echo "═══════════════════════════════════════════════════"
