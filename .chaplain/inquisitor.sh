#!/usr/bin/env bash
# .chaplain/inquisitor.sh — Audit loop: Quote → Investigate → Judge → Record
# FR-076: Quotes the Scripture, audits recent work, writes diary entry
# FR-118: --propose flag detects persistent violations and writes fix proposals to inbox
# Usage: .chaplain/inquisitor.sh [--propose]
set -euo pipefail
cd "$(dirname "$0")/.."

PROPOSE=""
if [[ "${1:-}" == "--propose" ]]; then
    PROPOSE="true"
fi

echo "🔍 Inquisitor: Auditing recent work against the Scripture..."

# Investigate & Judge — single copilot call
copilot --allow-all-paths --allow-all-tools -p "**Inquisit.**
You are the Inquisitor. Your duty: audit the project's recent work against the Scripture.

**Step 1 — Gather Evidence:**
- Read the latest 5 commits: git log --oneline -5
- Read the top of CHANGELOG.md (first 30 lines)
- Read the latest diary entry in docs/diary.md (first entry after the header)
- Read CLAUDE.md to refresh the Scripture (Commandments, Sermon, Rite of Correction)

**Step 2 — Investigate:**
For each recent commit, check:
1. Does it follow Conventional Commits? (Commandment 10)
2. Is there a corresponding CHANGELOG entry? (Commandment 10)
3. If it introduced a new capability, was a requirement added to ARCHITECTURE.md? (ADR-001)
4. If tests were added, do they have @pytest.mark.req tags? (ADR-001)
5. Was a diary entry written for the task? (Sermon: Distill)
6. Are there any noqa suppressions without CONF-XXX entries? (noqa Confessions)

**Step 3 — Judge:**
Classify each finding as:
- ✓ COMPLIANT — Doctrine followed
- ⚠ DRIFT — Minor deviation, no immediate harm
- ✗ VIOLATION — Doctrine broken, action needed

**Step 4 — Record:**
Append a new diary entry to docs/diary.md following the established format:
- Header: '## YYYY-MM-DD: Inquisitor Audit — [summary]'
- **Context:** What was audited and why
- **Findings:** List of ✓/⚠/✗ items (keep concise — max 5 most significant)
- **Heuristic:** One actionable lesson extracted
- **Seed:** One forward-looking question

If all findings are COMPLIANT, still record the audit — compliance is worth witnessing.
Do NOT create or modify any files other than docs/diary.md."

echo "✅ Inquisitor: Audit complete."

if [[ -n "$PROPOSE" ]]; then
    echo "📋 Inquisitor: Proposing fixes for persistent violations..."
    copilot --allow-all-paths --allow-all-tools -p "**Propose.**
You are the Inquisitor in propose mode. Your duty: convert persistent violations into fix proposals.

**Step 1 — Read diary:** Read up to the last 5 'Inquisitor Audit' entries from docs/diary.md.
**Step 2 — Detect persistence:** Identify ✗ VIOLATION items appearing in ≥2 consecutive audits.
**Step 3 — Classify:** For each persistent violation:
  - Micro-fix (status field, count, missing entry): propose a direct fix description
  - Structural gap (missing REQ-YG-XXX, absent test tags): propose an FR stub
**Step 4 — Write proposals:** For each persistent violation, write a markdown file to .chaplain/inbox/:
  - Filename: inquisitor-<violation-type>.md — use kebab-case, max 3 words, derived from the failing check name (e.g., inquisitor-architecture-count.md, inquisitor-fr-status-draft.md)
  - Skip if .chaplain/inbox/ already contains a file with the same name
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
