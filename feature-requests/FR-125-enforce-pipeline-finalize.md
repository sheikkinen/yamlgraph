# Feature Request: FR-125 Enforce Pipeline Post-Merge Finalization

**Priority:** HIGH
**Type:** Enhancement
**Status:** ✅ Implemented
**Effort:** 1 day
**Requested:** 2026-03-07

## Summary

Add a `finalize_merge.sh` script that runs after a PR from the enforce pipeline is merged, automating three post-merge obligations: CHANGELOG entry, FR status update, and diary reflection stub.

## Value Statement

Maintainers get automatic enforcement of Commandment 10 (CHANGELOG), FR status hygiene, and diary reflection stubs — eliminating the dominant defect pattern flagged across Inquisitor Audits XVIII–XIX.

## Problem

The `enforce_worktree.sh` pipeline (FR-106) automates code delivery through five phases: implement → test → pre-commit → commit → PR. But it stops at PR creation. Three systematic blind spots emerge after merge:

1. **CHANGELOG gap**: Three consecutive `feat:` commits (FR-118, FR-119, FR-121) merged without `[Unreleased]` entries. Commandment 10 ("let the CHANGELOG.md bear witness") violated systematically. FR-077/FR-083 fixed the pre-commit hook to *block* manual commits missing CHANGELOG — but the enforce pipeline commits with `--no-verify` (line 157 of `enforce_worktree.sh`), bypassing that gate entirely.

2. **FR status drift**: Feature requests stay "Approved" or "In Progress" after merge. FR-112's status remained "Draft" for 10 consecutive audits before manual fix (`1a73d06`). CALCIFIED-3's 10-audit lifespan proves manual discipline fails at scale.

3. **Diary reflection debt**: Features ship without the Sermon's Distill step. Inquisitor Audit entries are not substitutes for implementation reflections with Trap/Heuristic/Seed structure.

**Root cause**: The enforce pipeline's `--no-verify` commit (line 157) intentionally bypasses pre-commit hooks (since Phase 3 already ran them). This also bypasses the CHANGELOG enforcement hook (FR-077/FR-083). No post-merge step exists to compensate.

**Evidence**:
- Inquisitor Audits XVIII–XIX flagged the CHANGELOG pattern repeatedly
- FR-112 status stayed "Draft" for 10 audits before manual fix
- CALCIFIED-3 persisted for 10 audit cycles — manual remediation is unreliable

## Proposed Solution

A separate `scripts/finalize_merge.sh` script that runs after PR merge on the main branch. Separate from `enforce_worktree.sh` because finalization happens in a different lifecycle phase (post-merge on main, not pre-merge in worktree).

### Usage

```bash
# After merging a PR from the enforce pipeline:
scripts/finalize_merge.sh feature-requests/FR-125-enforce-pipeline-finalize.md
```

### Script flow

```bash
#!/usr/bin/env bash
set -euo pipefail

FR_PATH="$1"

# Validate: FR file exists, on main branch, branch is up-to-date
[[ -f "$FR_PATH" ]] || { echo "❌ FR file not found: $FR_PATH"; exit 1; }
git diff --quiet || { echo "❌ Working tree dirty"; exit 1; }
[[ "$(git branch --show-current)" == "main" ]] || { echo "❌ Not on main branch"; exit 1; }
git pull --ff-only

# Extract FR metadata
FR_HEADING=$(grep -m1 '^# ' "$FR_PATH" | sed 's/^#[# ]*//')
FR_NUM=$(basename "$FR_PATH" .md | grep -oE 'FR-[0-9]+')
# Strip "Feature Request: " prefix and FR number to get clean title
FR_TITLE=$(echo "$FR_HEADING" | sed 's/^Feature Request: //' | sed "s/^${FR_NUM} //")
REQ_ID=$(grep -oE 'REQ-YG-[0-9]+' "$FR_PATH" | head -1)

# Extract first content line from ## Summary for the CHANGELOG description
FR_SUMMARY=$(awk '/^## Summary/{found=1; next} found && /^[^ #]/{print; exit}' "$FR_PATH")

# --- Step 1: CHANGELOG entry ---
# Format: - **FR-NNN Title**: Summary sentence (REQ-YG-XXX)
ENTRY="- **${FR_NUM} ${FR_TITLE}**: ${FR_SUMMARY}"
[[ -n "$REQ_ID" ]] && ENTRY="${ENTRY} (${REQ_ID})"

# Duplicate guard — skip if FR already in CHANGELOG
if grep -q "$FR_NUM" CHANGELOG.md; then
    echo "⚠️  ${FR_NUM} already in CHANGELOG, skipping"
else
    # Find "### Added" under "## [Unreleased]" and insert after it
    ADDED_LINE=$(awk '/^## \[Unreleased\]/,/^## \[/' CHANGELOG.md | grep -n '### Added' | head -1 | cut -d: -f1)
    if [[ -n "$ADDED_LINE" ]]; then
        UNRELEASED_LINE=$(grep -n '^## \[Unreleased\]' CHANGELOG.md | head -1 | cut -d: -f1)
        INSERT_AT=$((UNRELEASED_LINE + ADDED_LINE - 1))
        # Portable in-place edit using temp file (sed -i incompatible across macOS/Linux)
        sed "${INSERT_AT}a\\
${ENTRY}
" CHANGELOG.md > CHANGELOG.md.tmp && mv CHANGELOG.md.tmp CHANGELOG.md
    else
        # No ### Added section yet — create one
        UNRELEASED_LINE=$(grep -n '^## \[Unreleased\]' CHANGELOG.md | head -1 | cut -d: -f1)
        sed "${UNRELEASED_LINE}a\\
\\
### Added\\
${ENTRY}
" CHANGELOG.md > CHANGELOG.md.tmp && mv CHANGELOG.md.tmp CHANGELOG.md
    fi
fi

# --- Step 2: FR status update ---
sed 's/^\*\*Status:\*\*.*/\*\*Status:\*\* ✅ Implemented/' "$FR_PATH" > "${FR_PATH}.tmp" && mv "${FR_PATH}.tmp" "$FR_PATH"

# --- Step 3: Diary reflection stub ---
DATE=$(date +%Y-%m-%d)
cat >> docs/diary.md << EOF

---

## ${DATE}: ${FR_NUM} — Implementation Reflection

**Context:** Implemented ${FR_TITLE}.

**Trap:** [What cognitive trap was encountered?]

**Heuristic:** [What lesson was learned?]

**Seed:** [What question remains?]
EOF

# --- Step 4: Commit finalization ---
git add CHANGELOG.md "$FR_PATH" docs/diary.md
cat > ./tmp/msg.txt << EOF
chore: ${FR_NUM} post-merge finalization

- CHANGELOG [Unreleased] entry added
- FR status updated to Implemented
- Diary reflection stub appended

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
EOF
git commit -F ./tmp/msg.txt

echo "✅ Finalization complete for ${FR_NUM}"
echo "📝 Edit docs/diary.md to fill in Trap/Heuristic/Seed"
```

### Integration with enforce_worktree.sh

Add finalize instructions to the "NEXT STEPS" output block (starts at line 175 of `enforce_worktree.sh`). Insert after line 189, before the trailing blank line:

```bash
echo -e "  ${YELLOW}After merging, finalize:${NC}"
echo "    git checkout main && git pull"
echo "    scripts/finalize_merge.sh $FR_PATH"
echo ""
```

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| Separate script (not Phase 6 of enforce) | Finalization runs on main after merge; enforce runs in worktree before merge. Different lifecycle phases. |
| Shell script (not Python or LLM) | All three operations are deterministic text transforms. No LLM needed. Keeps it fast and testable. |
| `chore:` commit type (not `feat:`) | Finalization is housekeeping, not a feature. Avoids triggering the CHANGELOG hook recursively. |
| Diary stub with placeholders | Humans fill in Trap/Heuristic/Seed. The stub prevents omission; the reflection requires thought. |
| `git pull --ff-only` guard | Ensures main is up-to-date before modifying shared files. Fails fast if behind. |
| Temp file for portable sed | `sed 'cmd' file > file.tmp && mv file.tmp file` works on both macOS and Linux, unlike `sed -i` which has incompatible syntax across platforms. |
| Multi-line commit via `tmp/msg.txt` | Convention from CLAUDE.md: avoids dquote traps with special characters in `-m` strings. |
| Summary extraction for CHANGELOG | Extracts first content line from `## Summary` instead of a static string, producing informative CHANGELOG entries consistent with existing format. |
| Duplicate-entry guard | `grep -q "$FR_NUM" CHANGELOG.md` prevents accidental double-runs from inserting duplicate entries. |
| `INSERT_AT` uses `ADDED_LINE - 1` | Corrects off-by-one: awk line 1 = `## [Unreleased]` header, so `ADDED_LINE` over-counts by 1. Subtracting yields the `### Added` header line, and `sed "Na\..."` inserts after line N. |

### Bugs fixed from Judgement review

| # | Issue | Fix |
|---|-------|-----|
| 1 | Off-by-one in CHANGELOG insertion — `INSERT_AT` pointed to first existing entry, not header | `INSERT_AT=$((UNRELEASED_LINE + ADDED_LINE - 1))` — inserts after `### Added` header |
| 2 | Static "Post-merge finalization" CHANGELOG description — redundant with title | Extract first sentence of `## Summary` from FR file via awk |
| 3 | Wrong line reference for NEXT STEPS block — FR said "after line 189" | Corrected: NEXT STEPS block starts at line 175; new content goes after line 189 (end of existing items) |
| 4 | No duplicate-entry guard — re-running script would insert duplicate CHANGELOG entry | Added `grep -q "$FR_NUM" CHANGELOG.md` guard with skip message |

### What changes

| File | Change |
|------|--------|
| `scripts/finalize_merge.sh` | New script (~70 lines) |
| `scripts/enforce_worktree.sh` | Add finalize command to "NEXT STEPS" output (3 lines, after line 189) |

### What does NOT change

- `enforce_worktree.sh` pipeline flow (Phases 1–5 unchanged)
- `.pre-commit-config.yaml` hooks (FR-077/FR-083 CHANGELOG hook unchanged)
- `.chaplain/watch.sh` (unrelated lifecycle)
- `docs/diary.md` format (entries follow existing structure)

## Acceptance Criteria

- [ ] `scripts/finalize_merge.sh <FR-path>` executes without error on a merged FR
- [ ] CHANGELOG.md `[Unreleased]` → `### Added` section contains new entry matching format `- **FR-NNN Title**: Summary sentence (REQ-YG-XXX)`
- [ ] CHANGELOG entry description is extracted from FR's `## Summary` section (not static text)
- [ ] CHANGELOG entry includes `(REQ-YG-XXX)` suffix only when FR file contains a requirement ID
- [ ] Duplicate CHANGELOG entry prevented when script is run twice for the same FR
- [ ] CHANGELOG entry inserted immediately after `### Added` header (not after first existing entry)
- [ ] FR file `**Status:**` line updated to `✅ Implemented`
- [ ] `docs/diary.md` has new stub entry with date, FR number, and placeholder Trap/Heuristic/Seed fields
- [ ] Finalization committed as `chore: FR-XXX post-merge finalization` via `tmp/msg.txt`
- [ ] Script fails fast with non-zero exit if: working tree dirty, not on main, or FR file missing
- [ ] `enforce_worktree.sh` "NEXT STEPS" block includes finalize command
- [ ] Script uses portable temp file pattern (no `sed -i`)
- [ ] Script header comments describe usage and prerequisites
- [ ] Unit test: shell script validates argument parsing and fail-fast guards
- [ ] Integration test: run finalize on a test FR file, assert CHANGELOG/status/diary changes

## Alternatives Considered

1. **Embed finalization in enforce_worktree.sh as Phase 6** — The enforce script runs in a worktree that gets cleaned up on exit. Post-merge finalization needs to run on main after the PR is merged. These are different lifecycle phases. Embedding would require removing the cleanup trap, waiting for merge, then finalizing — making the script long-running and fragile. Rejected.

2. **GitHub Actions workflow on PR merge** — Would automate fully, but adds CI infrastructure dependency for what is currently a local-first pipeline. Over-engineering for the current workflow. Could be a future enhancement. Rejected for now.

3. **Pre-commit hook that enforces CHANGELOG on `--no-verify` commits** — Contradictory: `--no-verify` exists specifically to bypass hooks. The real fix is post-merge finalization, not fighting the bypass. Rejected.

4. **LLM-generated diary entries (like FR-093)** — FR-093 uses LLM for Chaplain diary entries because Plan→Judge sessions produce rich context. Enforce pipeline finalization is deterministic — the stub just needs placeholders. An LLM call would add latency and non-determinism for no benefit. Rejected.

5. **Merge finalization into `watch.sh` polling loop** — `watch.sh` monitors `.chaplain/inbox/` for new work, not merged PRs. Overloading it with post-merge duties conflates two concerns. Rejected.

## Related

- `scripts/enforce_worktree.sh` — Pipeline that creates PRs (stops before finalization)
- `feature-requests/FR-077-changelog-commit-enforcement.md` — CHANGELOG pre-commit hook (implemented, but bypassed by `--no-verify`)
- `feature-requests/FR-083-changelog-hook-fix.md` — Fixed $0/$1 bug in CHANGELOG hook (implemented)
- `feature-requests/FR-093-chaplain-diary-append.md` — Chaplain diary automation (different lifecycle)
- `feature-requests/FR-106-parallel-worktree-pipeline.md` — Original enforce pipeline FR
- `docs/diary.md` — Inquisitor Audits XVIII–XIX documenting the CHANGELOG gap pattern
