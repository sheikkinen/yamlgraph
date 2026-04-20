# Feature Request: FR-258 Automate Post-Merge Finalization in watch.sh

**Priority:** HIGH
**Type:** Enhancement
**Status:** ✅ Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-20

## Summary

Add a post-merge detection phase to `.chaplain/watch.sh` that automatically creates finalization PRs for recently merged feature PRs, eliminating the last manual step in the Chaplain's closed-loop pipeline.

## Value Statement

Pipeline operators gain a fully autonomous Plan→Judge→Enforce→Merge→Finalize loop, removing the human-forgetting failure mode that currently requires Inquisitor post-hoc detection (Level 2) instead of self-healing (Level 3).

## Problem

Every PR merged to `main` requires a manual `scripts/finalize_merge.sh <FR-path>` invocation to create:
1. A changelog fragment in `changelog/unreleased/`
2. FR status update to "✅ Implemented"
3. A diary reflection stub in `docs/diary/`

This is the single remaining manual step in the otherwise fully automated Chaplain pipeline. The human-forgetting failure mode is well-documented: 59 Inquisitor findings, 65 unfinalized FRs, and the `detection_without_enforcement` pattern has exceeded the `audit_as_ritual` threshold by 10×.

Current flow:
```
watch.sh → graph (Plan/Judge) → enforce_worktree.sh → PR created → [human merges] → [human runs finalize_merge.sh]
```

Target flow:
```
watch.sh → graph (Plan/Judge) → enforce_worktree.sh → PR created → [human merges] → watch.sh detects merge → finalization PR created & auto-merged
```

## Proposed Solution

### Phase placement

Add the finalization phase to the `watch.sh` main loop **after the metrics block** (line 141) and **before the loop's final `echo`** (line 143). This ensures:
- Enforcement and its metrics are complete before finalization runs
- The main inbox-processing flow is unaffected
- Finalization can be separately instrumented (FR-256 extension)

### Shared library extraction (Judge Issue 2)

Extract the duplicated finalization logic into `.chaplain/lib/finalize_lib.sh`:
- FR metadata extraction (`FR_HEADING`, `FR_NUM`, `FR_TITLE`, `REQ_ID`, `FR_SUMMARY`)
- Changelog fragment generation (YAML frontmatter + entry)
- FR status `sed` update
- Diary stub creation

Both `scripts/finalize_merge.sh` and the `watch.sh` finalization phase source this library. The main-branch guard stays in `finalize_merge.sh` where it belongs.

### PR-based finalization (Judge Issue 1)

Direct push to `main` is forbidden by branch protection. The finalization phase creates a PR instead:
1. Creates branch `chore/finalize-fr-NNN` from `main`
2. Generates changelog fragment, FR status update, and diary stub via shared library
3. Commits (without `--no-verify` — hooks run normally; `chore` type passes all gates)
4. Pushes branch, creates PR via `gh pr create`
5. Enables auto-merge via `gh pr merge --auto --squash`

CI gate analysis for `chore` commit type:
- `commitlint`: `chore` is an allowed type ✅
- `test`: No code changes, tests pass ✅
- `changelog-gate`: Only blocks `feat`/`fix` PRs ✅
- `diary-gate`: Only blocks `feat`/`fix` PRs with `FR-XXX` ✅
- `demo-gate`: Only for `feat`/`fix` modifying `examples/demos/` ✅
- `conflict-check`, `security`: Unaffected ✅

### Timestamp-based filtering (Judge Issue 2 — silent omissions)

Replace fixed-window `--limit N` with persistent timestamp via `.chaplain/state/last-finalized-at`:
1. Read timestamp from file (default to 24 hours ago if missing)
2. Query `gh pr list --state merged --search "merged:>TIMESTAMP"`
3. After processing, write current timestamp to file

This eliminates the fixed-window problem: even if `watch.sh` is down for days, it catches all missed merges on restart.

### Idempotency guards (three layers)

1. **FR status check**: Skip if FR already marked "✅ Implemented"
2. **Existing PR check**: Skip if `chore/finalize-fr-NNN` PR already open
3. **Existing fragment check**: Skip if changelog fragment file already exists

### Implementation sketch

```bash
# .chaplain/lib/finalize_lib.sh — Shared finalization functions

# Extract FR metadata from FR file path
# Sets: FR_HEADING, FR_NUM, FR_TITLE, REQ_ID, FR_SUMMARY
extract_fr_metadata() {
    local fr_path="$1"
    FR_HEADING=$(grep -m1 '^# ' "$fr_path" | sed 's/^#[# ]*//')
    FR_NUM=$(basename "$fr_path" .md | grep -oE 'FR-[0-9]+')
    FR_TITLE=$(echo "$FR_HEADING" | sed 's/^Feature Request: //' | sed "s/^${FR_NUM} //")
    REQ_ID=$(grep -oE 'REQ-YG-[0-9]+' "$fr_path" | head -1 || true)
    FR_SUMMARY=$(awk '/^## Summary/{found=1; next} found && /^[^ #]/{print; exit}' "$fr_path")
}

# Create changelog fragment — idempotent (skips if exists)
create_changelog_fragment() {
    local fr_num="$1" fr_title="$2" fr_summary="$3" req_id="$4"
    local slug entry req_line frag_path
    slug=$(echo "$fr_title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
    frag_path="changelog/unreleased/${fr_num}-${slug}.md"
    mkdir -p changelog/unreleased
    [[ -f "$frag_path" ]] && return 0
    entry="- **${fr_num} ${fr_title}**: ${fr_summary}"
    [[ -n "$req_id" ]] && entry="${entry} (${req_id})"
    req_line=""
    [[ -n "$req_id" ]] && req_line="req: ${req_id}"
    cat > "$frag_path" << FRAGMENT
---
type: feat
scope: ${slug%%-*}
${req_line}
---
${entry}
FRAGMENT
}

# Update FR status to Implemented
update_fr_status() {
    local fr_path="$1"
    sed 's/^\*\*Status:\*\*.*/\*\*Status:\*\* ✅ Implemented/' "$fr_path" > "${fr_path}.tmp" \
        && mv "${fr_path}.tmp" "$fr_path"
}

# Create diary reflection stub — idempotent (skips if exists)
create_diary_stub() {
    local fr_num="$1" fr_title="$2"
    local diary_date diary_entry
    diary_date=$(date +%Y-%m-%d)
    mkdir -p docs/diary
    diary_entry="docs/diary/${diary_date}-reflection-${fr_num}.md"
    [[ -f "$diary_entry" ]] && return 0
    cat > "$diary_entry" << DIARY
## ${diary_date}: ${fr_num} — Implementation Reflection

**Context:** Implemented ${fr_title}.

**Trap:** [What cognitive trap was encountered?]

**Heuristic:** [What lesson was learned?]

**Seed:** [What question remains?]
DIARY
}
```

In `watch.sh`, after the metrics block:

```bash
# ── FR-258: Post-merge finalization ──────────────────────────────────────
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    git checkout main --quiet 2>/dev/null || true
    git pull --quiet 2>/dev/null || true

    STATE_DIR=".chaplain/state"
    mkdir -p "$STATE_DIR"
    LAST_CHECK_FILE="$STATE_DIR/last-finalized-at"
    if [[ -f "$LAST_CHECK_FILE" ]]; then
        SINCE=$(cat "$LAST_CHECK_FILE")
    else
        SINCE=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
            || date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
    fi

    source .chaplain/lib/finalize_lib.sh

    gh pr list --state merged --search "merged:>=$SINCE" \
        --json number,headRefName,mergedAt \
        --jq '.[].headRefName' 2>/dev/null \
    | while read -r branch; do
        fr_num=$(echo "$branch" | grep -oiE 'fr-[0-9]+' | head -1) || continue
        [[ -z "$fr_num" ]] && continue

        fr_file=$(find feature-requests/ -maxdepth 1 -iname "${fr_num}-*.md" \
            -type f 2>/dev/null | head -1)
        [[ -z "$fr_file" ]] && continue
        grep -q 'Status.*Implemented' "$fr_file" 2>/dev/null && continue

        fin_branch="chore/finalize-${fr_num,,}"
        if gh pr list --state open --head "$fin_branch" --json number \
            --jq 'length' 2>/dev/null | grep -q '[1-9]'; then
            continue
        fi

        echo "🔄 Creating finalization PR for: $fr_file"
        git checkout -b "$fin_branch" main --quiet 2>/dev/null || {
            echo "⚠️  Branch $fin_branch already exists, skipping"
            git checkout main --quiet 2>/dev/null || true
            continue
        }

        extract_fr_metadata "$fr_file"
        create_changelog_fragment "$FR_NUM" "$FR_TITLE" "$FR_SUMMARY" "$REQ_ID"
        update_fr_status "$fr_file"
        create_diary_stub "$FR_NUM" "$FR_TITLE"

        git add changelog/unreleased/ "$fr_file"
        mkdir -p ./tmp
        cat > ./tmp/msg.txt << CMSG
chore: ${FR_NUM} post-merge finalization

- Changelog fragment created in changelog/unreleased/
- FR status updated to Implemented
- Diary reflection stub created (untracked)
CMSG
        git commit -F ./tmp/msg.txt 2>/dev/null || {
            echo "⚠️  Nothing to commit for $fr_file"
            git checkout main --quiet 2>/dev/null || true
            git branch -D "$fin_branch" 2>/dev/null || true
            continue
        }

        git push origin "$fin_branch" --quiet 2>/dev/null && \
        gh pr create --base main --head "$fin_branch" \
            --title "chore: ${FR_NUM} post-merge finalization" \
            --body "Auto-generated by watch.sh (FR-258)." \
            2>/dev/null && \
        gh pr merge "$fin_branch" --auto --squash 2>/dev/null || {
            echo "⚠️  Finalization PR creation failed for $fr_file"
        }

        git checkout main --quiet 2>/dev/null || true
    done

    date -u +%Y-%m-%dT%H:%M:%SZ > "$LAST_CHECK_FILE" 2>/dev/null || true
fi
```

### Key Design Decisions

1. **PR-based, not direct push**: Respects branch protection. `chore` PRs pass all CI gates.
2. **Shared library, not inline duplication**: `.chaplain/lib/finalize_lib.sh` prevents drift between `finalize_merge.sh` and `watch.sh` (Judge Issue 2, Commandment 8).
3. **No `--no-verify`**: Hooks run normally (Judge Issue 1, Scripture absolute rule).
4. **Timestamp-based window**: `.chaplain/state/last-finalized-at` eliminates the silent-omission gap.
5. **Three idempotency guards**: FR status, existing PR, existing fragment.
6. **Sequential processing**: Consistent with FR-175 lesson.
7. **Failure isolation**: Failed finalization logs warning without blocking the main loop.

## Acceptance Criteria

- [x] Shared library `.chaplain/lib/finalize_lib.sh` extracted with functions: `extract_fr_metadata`, `create_changelog_fragment`, `update_fr_status`, `create_diary_stub`
- [x] `scripts/finalize_merge.sh` refactored to source the shared library (behavior unchanged)
- [x] `watch.sh` detects recently merged PRs with unfinalized FRs on each poll cycle
- [x] A finalization PR is created for each unfinalized FR (branch: `chore/finalize-fr-NNN`)
- [x] Auto-merge is enabled on finalization PRs via `gh pr merge --auto --squash`
- [x] Changelog fragment, FR status update, and diary stub are included in the PR
- [x] Already-finalized FRs (status "✅ Implemented") are skipped
- [x] No duplicate finalization PRs on repeated polling cycles (idempotent)
- [x] Timestamp-based filtering via `.chaplain/state/last-finalized-at` prevents silent omissions
- [x] On first run (no timestamp file), defaults to 24-hour lookback window
- [x] Non-FR branches (e.g., `chore/...`, `docs/...`) are safely ignored
- [x] Failed finalizations log a warning without blocking the main loop
- [x] `watch.sh` returns to `main` branch after finalization phase completes
- [x] No `--no-verify` flag used anywhere in the implementation
- [x] `.chaplain/state/` added to `.gitignore` (local daemon state, not committed)
- [x] Existing manual `finalize_merge.sh` still works unchanged
- [x] Tests added for shared library functions (FR-path derivation, slug generation)
- [x] Documentation updated

## Alternatives Considered

### Direct push with admin bypass

Use admin credentials to push finalization commits directly to `main`. **Rejected:** violates `automation_inherits_doctrine` and branch protection principles. Break-glass is for emergencies, not routine automation.

### GitHub Actions workflow

A `push` event workflow on `main` that detects merged feat PRs and creates finalization PRs. **Rejected:** fragments the Chaplain pipeline across two systems. `watch.sh` already satisfies all preconditions.

### Calling `finalize_merge.sh` directly

Run the existing script from a branch context. **Rejected:** the script has a `main`-branch guard. Modifying it would change the manual workflow contract. The shared library approach (Judge Issue 2) is superior to either direct invocation or inline duplication.

### Fixed-window `--limit 10`

Use `gh pr list --state merged --limit 10` without persistent state. **Rejected:** silent omissions when `watch.sh` is down longer than the window covers. Timestamp file is ~3 lines for complete coverage.

## Related

- **FR-125**: Original `finalize_merge.sh` implementation (CAP-38, REQ-YG-125)
- **FR-179**: Append-only changelog fragments
- **FR-175**: Sequential enforcement in `watch.sh`
- **FR-243**: GitHub Issue sync in `watch.sh` (same polling pattern)
- **FR-256**: Pipeline timing metrics (instrumentation point)
- **FR-150**: Branch protection rules (constraint this FR respects)
- **GitHub Issue #137**: Originating proposal
- `scripts/finalize_merge.sh`: Manual finalization script (refactored to use shared library)
- `.chaplain/watch.sh`: Target file for modification
- `.chaplain/lib/finalize_lib.sh`: New shared library
- `.chaplain/state/`: New persistent state directory for timestamp tracking

## Judge's Verdict

**APPROVE** — Scope frozen. Authority granted.

**Classification:** Infrastructure automation — real problem (43+ unfinalized approved FRs confirmed), proven failure mode (`audit_as_ritual` threshold exceeded), established extension point (`watch.sh` with 36 FR references).

**Evaluation:**

1. **Scope:** Clear, minimal, single-concern. Library extraction, watch.sh integration, and timestamp filtering are tightly coupled — no split warranted.
2. **Contradictions:** None found. PR-based approach correctly respects branch protection. CI gate analysis verified: `changelog-gate`, `diary-gate`, and `demo-gate` all use `startsWith(…, 'feat') || startsWith(…, 'fix')` guards, confirming `chore` PRs pass unconditionally.
3. **Acceptance criteria:** All 16 criteria are concrete and testable.
4. **Feasibility:** Implementation sketch is nearly complete. All building blocks exist inline in `finalize_merge.sh`. The `watch.sh` polling pattern is established by FR-243.
5. **Architecture alignment:** Follows shared library pattern (`.chaplain/lib/diary.py` precedent), sequential processing (FR-175), and PR-based enforcement (FR-150).

**Implementation notes (address during enforcement, not scope changes):**

1. **`.chaplain/state/` must be gitignored.** The timestamp file is local daemon state — add to `.gitignore`. Add an acceptance criterion.
2. **Bash 4+ portability:** `${fr_num,,}` (lowercase expansion) requires bash 4+. Stock macOS ships 3.2. Use `$(echo "$fr_num" | tr '[:upper:]' '[:lower:]')` instead.
3. **Statistics note:** FR claims "18 of 19 (94.7%)" but current audit shows 43 unfinalized approved FRs out of 183 with status. Problem is real regardless — the magnitude is even larger than stated.
4. **Empty `req_line` in YAML frontmatter:** When `REQ_ID` is empty, the heredoc emits a blank line. Pre-existing in `finalize_merge.sh` — fix in the shared library extraction (conditional block, not blank line).

## Research Brief

### Existing Abstractions

- **`scripts/finalize_merge.sh`** (114 lines, FR-125): Contains all four proposed library functions inline — `extract_fr_metadata` (lines 36–43), `create_changelog_fragment` (lines 45–71), `update_fr_status` (lines 73–75), `create_diary_stub` (lines 77–96). Two idempotency guards present (fragment exists, diary stub exists); missing the "existing PR" guard.
- **`.chaplain/watch.sh`** (144 lines): Main daemon loop with five phases — GitHub Issues sync (FR-243, lines 25–53), local inbox poll (55–56), FR generation (60–72), FR routing with sequential enforcement (FR-175, lines 78–102), GitHub Issue close (104–114), and metrics (FR-256, lines 117–141). No post-merge detection phase exists.
- **`.chaplain/lib/diary.py`**: Shared Python library for diary writing (FR-097/FR-134). Establishes the `lib/` extraction pattern that FR-258 would extend with shell equivalents. No `.chaplain/lib/finalize_lib.sh` exists yet.
- **`.chaplain/state/`**: Directory does not exist. No timestamp-based filtering infrastructure in place.
- **`enforce_worktree.sh` / `bugfix_worktree.sh`** (lines 206–208): Both print manual `finalize_merge.sh` instructions post-PR-creation — the exact manual step FR-258 automates.
- **`.chaplain/inquisitor.sh`** (116 lines): Audits for CHANGELOG/diary gaps but has no blocking mechanism — detection without enforcement.

### Diary Precedents

- **`parallelism_theatre`** (2026-03-09, FR-175 reflection): Original `watch.sh` used `nohup ... &` causing race conditions on shared files (CHANGELOG, ARCHITECTURE.md). Cure: sequential processing. FR-258 must serialize finalization to avoid the same CHANGELOG/diary conflicts.
- **`automation_inherits_doctrine`** (2026-03-13 Audit 122, 2026-03-14 Audit 125): Scripts must follow same rules as humans — no `--no-verify`, no phantom authors, no direct pushes. Third consecutive audit flagging phantom `Test <test@test.com>` author. FR-258 design correctly uses PR-based flow.
- **`detection_without_enforcement` → `audit_as_ritual`** (2026-03-08 Audit XXXVIII–XXXIX, 2026-03-14 Audit 125): 59 Inquisitor findings for missing changelog/diary, 65 unfinalized FRs. Audit count exceeds `audit_as_ritual` threshold (3+) by 10×. This is the primary motivation for FR-258.
- **"Remediation breeds unremediated tasks"** (2026-03-08 Audit XXXVIII): FR-152 was created to fix missing diary entries, but its own commits shipped without diary entries. The finalization cycle repeats because it depends on human memory.
- **Branch protection as pre-merge boundary** (2026-03-08, FR-150 reflection): Enforcement must block at merge boundary, not downstream. FR-258's PR-based approach is correct — `chore` commits pass all CI gates without exemptions.
- **Idempotency from source of truth** (2026-03-28, FR-207 reflection): Systems are naturally idempotent when state is re-derived from source. FR-258's three guards (FR status, existing PR, existing fragment) follow this pattern.
- **FR-243 remote inbox pattern** (2026-04-20 reflection): Extended `watch.sh` with GitHub API polling — same architectural pattern FR-258 uses for merged PR detection. Validates the polling approach within `watch.sh`.

### Usage Evidence

- Existing graphs using related abstractions: **0** (FR-258 modifies infrastructure scripts, not YAML graphs)
- Unfinalized implemented FRs: **18 of 19 (94.7%)** — including FR-125 (the script that implements finalization itself)
- Inquisitor audit entries documenting the gap: **216 diary entries**, 21 explicit mentions of finalization/changelog/diary gaps
- Feature requests referencing `watch.sh`: **36** (established extension point)
- Shared library precedent: **1** (`.chaplain/lib/diary.py` — Python; FR-258 adds shell equivalent)
- Real-world use cases beyond the proposal: Every merged `feat`/`fix` PR requires finalization; the 94.7% failure rate proves the manual workflow is broken

### Classification Signal

- Abstraction level: **integration** (Chaplain daemon automation, not a framework primitive consumed by YAML graphs)
- Recommended approach: **build** (problem is quantified at 94.7% failure rate; shared library extraction reduces duplication; `watch.sh` is an established extension point with 36 FR references; all building blocks exist inline in `finalize_merge.sh`)
- Key risk: Finalization PRs conflicting with concurrent enforcement PRs on shared files (CHANGELOG, diary) — mitigated by sequential processing (FR-175 lesson) and the `chore` commit type passing all CI gates without changelog/diary gates
