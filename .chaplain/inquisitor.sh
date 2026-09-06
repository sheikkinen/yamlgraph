#!/usr/bin/env bash
# .chaplain/inquisitor.sh — Audit loop: Quote → Investigate → Judge → Record
# FR-076: Quotes the Scripture, audits recent work, writes diary entry
# FR-118: --propose flag detects persistent violations and writes fix proposals to inbox
# FR-131: Commit-delta gate aborts when no feat/fix commits since last audit
# FR-142: Worktree gate suppresses audit in git worktrees (enforce pipeline)
# Usage: .chaplain/inquisitor.sh [--force] [--propose]
set -euo pipefail
cd "$(dirname "$0")/.."

FORCE=""
PROPOSE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --force) FORCE="true"; shift ;;
        --propose) PROPOSE="true"; shift ;;
        *) shift ;;
    esac
done

# --- Worktree gate (FR-142) ---
# In a git worktree, .git is a file (gitdir pointer), not a directory.
# Suppress audit during enforce pipeline — intermediate commits are WIP.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$REPO_ROOT" && -f "$REPO_ROOT/.git" && -z "$FORCE" ]]; then
    echo "⏭️  Inquisitor: Running in a git worktree (enforce pipeline in progress). Skipping audit."
    echo "   Audits run on main after the FR/PR is merged. Use --force to override."
    exit 0
fi

# --- Commit-delta gate (FR-131, FR-134) ---
# Extract HEAD SHA from the last audit's commit range in docs/diary/.
# Scan inquisitor-audit files sorted by name (most recent first).
LATEST_AUDIT=$(ls docs/diary/*inquisitor-audit* 2>/dev/null || true)
LATEST_AUDIT=$(echo "$LATEST_AUDIT" | sort -r | head -1)
if [[ -n "$LATEST_AUDIT" ]]; then
    LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\.\.`([a-f0-9]{7,})`.*/\2/p' "$LATEST_AUDIT" 2>/dev/null | head -1)
else
    LAST_SHA=""
fi
if [[ -n "$LAST_SHA" ]] && git rev-parse --verify "$LAST_SHA^{commit}" >/dev/null 2>&1; then
    ACTIONABLE=$(git log --oneline "$LAST_SHA"..HEAD | grep -cE '^[a-f0-9]+ (feat|fix)' || true)
    if [[ "$ACTIONABLE" -eq 0 && -z "$FORCE" ]]; then
        echo "⏭️  Inquisitor: No feat/fix commits since last audit ($LAST_SHA..HEAD). Nothing to audit."
        echo "   Use --force to override."
        exit 0
    fi
fi

echo "🔍 Inquisitor: Auditing recent work against the Scripture..."

# Investigate & Judge — single copilot call
copilot --allow-all-paths --allow-all-tools -p "**Inquisit.**
You are the Inquisitor. Your duty: audit the project's recent work against the Scripture.

**Step 1 — Gather Evidence:**
- Read the latest 5 commits: git log --oneline -5
- Read the top of CHANGELOG.md (first 30 lines)
- Read the latest diary entry from docs/diary/ (most recent file by name)
- Read CLAUDE.md to refresh the Scripture (Commandments, Sermon)

**Step 2 — Investigate:**
For each recent commit, check:
1. Does it follow Conventional Commits? (Commandment 10)
2. Is there a corresponding CHANGELOG entry? (Commandment 10)
3. If it introduced a new capability, was a requirement added to ARCHITECTURE.md? (ADR-001)
4. If framework-scope tests were added under tests/unit or tests/integration, do they have @pytest.mark.req tags? Treat .github/hooks/tests as infrastructure scope exempt from REQ-YG marker enforcement. (ADR-001)
5. Was a diary entry written for the task? (Sermon: Distill)
6. Are there any noqa suppressions without CONF-XXX entries? (noqa Confessions)

**Step 3 — Judge:**
Classify each finding as:
- ✓ COMPLIANT — Doctrine followed
- ⚠ DRIFT — Minor deviation, no immediate harm
- ✗ VIOLATION — Doctrine broken, action needed

**Step 4 — Record:**
Create a new diary entry file at docs/diary/YYYY-MM-DD-inquisitor-audit-<number>.md following the format:
- Header: '## YYYY-MM-DD: Inquisitor Audit — [summary]'
- **Context:** What was audited and why
- **Findings:** List of ✓/⚠/✗ items (keep concise — max 5 most significant)
- **Heuristic:** One actionable lesson extracted
- **Seed:** One forward-looking question

If all findings are COMPLIANT, still record the audit — compliance is worth witnessing.
Do NOT create or modify any files other than docs/diary/."

echo "✅ Inquisitor: Audit complete."

if [[ -n "$PROPOSE" ]]; then
    echo "📋 Inquisitor: Proposing fixes for persistent violations..."
    copilot --allow-all-paths --allow-all-tools -p "**Propose.**
You are the Inquisitor in propose mode. Your duty: convert persistent violations into fix proposals.

**Step 1 — Read diary:** Read up to the last 5 'Inquisitor Audit' entries from docs/diary/*inquisitor-audit* files (sorted by name, most recent first).
**Step 2 — Detect persistence:** Identify ✗ VIOLATION items appearing in ≥2 consecutive audits.
**Step 3 — Classify:** For each persistent violation:
  - Micro-fix (status field, count, missing entry): propose a direct fix description
  - Structural gap (missing REQ-YG-XXX, absent test tags): propose an FR stub
**Step 4 — Write proposals:** For each persistent violation, write a markdown file to .chaplain/inbox/:
  - Filename: inquisitor-<violation-type>.md — use kebab-case, max 3 words, derived from the failing check name (e.g., inquisitor-architecture-count.md, inquisitor-fr-status-draft.md)
  - Skip if .chaplain/inbox/ or ./feature-requests already contains a file with the same intent
  - Format:
    \`\`\`
    # Fix: [Brief violation description]

    ## Violation
    [What the inquisitor found, which audits flagged it]

    ## Suggested Fix
    [Concrete steps — for micro-fixes: the exact change; for structural gaps: an FR outline]
    \`\`\`
**Step 5 — Report:** Print a summary of proposals written (or 'No persistent violations found')."
    echo "✅ Inquisitor: Propose complete."
fi
