# Feature Request: FR-076 Chaplain Inquisitor

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-23

## Summary

A new `.chaplain/inquisitor.sh` script that audits the project's recent state — latest commit, CHANGELOG, diary — against the Scripture, and records its findings as a diary entry.

## Problem

The `watch.sh` loop automates *planning* (inbox → FR). But there is no automated *reflection* — no scheduled audit that asks: "Did the last change obey the doctrine?" The Scripture demands distillation after every task list (Commandment 10, Sermon: Distill), yet this depends on human memory. Entropy accumulates silently between Plan cycles.

The diary's Git Report entry (2026-02-23) was manually triggered. The Judge's Trap entry was discovered by accident during an unrelated FR. Neither would have surfaced without a human choosing to look. An Inquisitor formalizes this look.

## Proposed Solution

A shell script that mirrors `watch.sh`'s pattern: thin shell, all intelligence delegated to `copilot`.

### `.chaplain/inquisitor.sh`

```bash
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
```

### Flow

```
Scripture (CLAUDE.md)
    ↓ Quote
Recent state (git log, CHANGELOG, diary)
    ↓ Investigate
Findings (✓/⚠/✗)
    ↓ Judge
docs/diary.md (new entry appended)
```

### Usage

```bash
# One-shot audit
.chaplain/inquisitor.sh

# Scheduled (e.g., daily cron or after watch.sh completes a cycle)
# Can be chained: watch.sh processes inbox, then inquisitor.sh audits
```

## Constraints

1. **Shell stays thin** — No file ops in bash; all logic in the copilot prompt (same pattern as `watch.sh`).
2. **Read-only except diary** — The Inquisitor only writes to `docs/diary.md`. It does not fix violations; it records them. Fixes are the domain of Plan → Judge.
3. **No infinite loops** — Unlike `watch.sh`, this is a one-shot script. Run it manually or on schedule.
4. **Diary format preserved** — New entries follow the established `## Date: Title` / Context / [Findings] / Heuristic / Seed structure (middle sections vary by entry type).
5. **Scripture is source of truth** — The audit checks against CLAUDE.md and the custom instructions, not invented rules.

## Acceptance Criteria

- [x] `inquisitor.sh` exists at `.chaplain/inquisitor.sh` and is executable
- [x] Script delegates all intelligence to `copilot` (no file ops in shell)
- [x] Copilot reads: latest commits, CHANGELOG, diary, Scripture
- [x] Copilot classifies findings as ✓ COMPLIANT / ⚠ DRIFT / ✗ VIOLATION
- [x] Copilot appends exactly one new diary entry to `docs/diary.md`
- [x] Diary entry follows established format (Date header, Context, Findings, Heuristic, Seed)
- [x] Script is one-shot (exits after single audit)
- [x] No files modified except `docs/diary.md`
- [x] No unit tests needed (shell wrapper; all logic in copilot prompt)
- [x] No documentation updates needed (self-contained operational script)

## Alternatives Considered

1. **YAMLGraph pipeline** — Could build this as a YAML graph with tool nodes for git/file reading. Overkill for v1; the shell+copilot pattern from FR-068 is proven and minimal.
2. **Integrate into watch.sh** — Run audit after each Plan→Judge cycle. Rejected: separating concerns keeps each script single-purpose. Can be composed externally.
3. **Scheduled CI job** — Run inquisitor in CI on push. Interesting for future but requires CI copilot access. Record as seed.

## Phase 2: Pre-commit Background Trigger

**Status:** Planned

### Problem

The inquisitor requires manual invocation. Developers forget to run it. Doctrine drifts silently between audits.

### Solution

Add a pre-commit hook that spawns the inquisitor as a background process. The commit proceeds immediately; the audit runs asynchronously and writes findings to diary for the *next* commit to surface.

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml (add to local hooks)
- repo: local
  hooks:
    - id: inquisitor-background
      name: inquisitor (async audit)
      entry: bash -c 'nohup .chaplain/inquisitor.sh > .chaplain/inquisitor.log 2>&1 &'
      language: system
      pass_filenames: false
      always_run: true
      stages: [post-commit]  # Run AFTER commit succeeds
```

**Key details:**
- **`post-commit` stage** — Doesn't block the commit; runs after success
- **`nohup ... &`** — Detaches from terminal, survives hook exit
- **`.chaplain/inquisitor.log`** — Captures output for debugging (gitignored)

### .gitignore Addition

```
.chaplain/inquisitor.log
```

### Flow

```
Developer commits
    ↓ (pre-commit hooks run synchronously)
Commit succeeds
    ↓ (post-commit hook triggers)
inquisitor.sh spawns in background
    ↓ (developer continues working)
Audit completes
    ↓
docs/diary.md updated
    ↓ (next commit shows diary change)
Developer sees "modified: docs/diary.md" in next git status
```

### Acceptance Criteria (Phase 2)

- [x] Add `inquisitor-background` hook to `.pre-commit-config.yaml`
- [x] Hook uses `post-commit` stage
- [x] Hook spawns background process (`nohup ... &`)
- [x] Output redirected to `.chaplain/inquisitor.log`
- [x] `.chaplain/inquisitor.log` added to `.gitignore`
- [ ] Diary entry appears in `git status` of next commit

### Constraints

- **Non-blocking** — Commit must not wait for audit
- **Fail-safe** — If inquisitor fails, commit still succeeded; developer sees error in log
- **Single instance** — If inquisitor already running, second invocation should exit early (optional: `flock` guard)

## Related

- `.chaplain/watch.sh` — FR-068, the Plan→Judge loop this mirrors
- `docs/diary.md` — Output target
- `CLAUDE.md` — The Scripture being audited against
- Commandment 10: "Every failure shalt refine the law"
- Sermon: Distill — "After completing a task list, add a metacognitive entry"
