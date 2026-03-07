#!/usr/bin/env bash
# demo_detect.sh — Demonstrates FR-116 detection logic in isolation
#
# Usage:
#   examples/demos/watch-enforce/demo_detect.sh
#
# This demo creates a temporary workspace, simulates the before/after
# snapshot logic from watch.sh, and shows how new FRs are detected,
# rejected FRs are skipped, and enforce would be spawned.
set -euo pipefail

DEMO_DIR=$(mktemp -d)
trap 'rm -rf "$DEMO_DIR"' EXIT

echo "📁 Demo workspace: $DEMO_DIR"
echo ""

# --- Setup: pre-existing FR ---
mkdir -p "$DEMO_DIR/feature-requests"
cat > "$DEMO_DIR/feature-requests/FR-001-existing.md" <<'EOF'
# FR-001: Existing Feature
**Status:** Approved
Already implemented.
EOF

echo "=== Scenario 1: No new FR ==="
cd "$DEMO_DIR"
before=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
# (simulate graph run — no new file created)
after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)
if [[ -z "$new_fr" ]]; then
    echo "   ✅ No new FR detected — polling loop continues"
fi
echo ""

echo "=== Scenario 2: New approved FR ==="
before=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
# (simulate graph creating a new FR)
cat > "$DEMO_DIR/feature-requests/FR-116-watch-enforce.md" <<'EOF'
# FR-116: Watch→Enforce Integration
**Status:** Approved
Spawn enforce on new FR.
EOF
after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)
if [[ -n "$new_fr" ]]; then
    if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
        echo "   ⏭️  Skipping rejected FR: $new_fr"
    else
        echo "   🚀 Would spawn: scripts/enforce_worktree.sh $new_fr"
        mkdir -p tmp
        LOG="tmp/enforce-$(basename "$new_fr" .md).log"
        echo "   📝 Log would go to: $LOG"
    fi
fi
echo ""

echo "=== Scenario 3: New rejected FR ==="
before=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
cat > "$DEMO_DIR/feature-requests/FR-999-bad-idea.md" <<'EOF'
# FR-999: Bad Idea
**Status:** Rejected
Not viable.
EOF
after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)
if [[ -n "$new_fr" ]]; then
    if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
        echo "   ⏭️  Skipping rejected FR: $new_fr"
    else
        echo "   🚀 Would spawn: scripts/enforce_worktree.sh $new_fr"
    fi
fi
echo ""

echo "✅ Demo complete — all three scenarios exercised."
