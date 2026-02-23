#!/usr/bin/env bash
# .chaplain/inquisitor.sh — Audit loop: Quote → Investigate → Judge → Record
# FR-076: Quotes the Scripture, audits recent work, writes diary entry
set -euo pipefail
cd "$(dirname "$0")/.."

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
