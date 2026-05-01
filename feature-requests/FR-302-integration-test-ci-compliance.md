# Feature Request: FR-302 Integration Test CI Compliance

**Priority:** HIGH
**Type:** Enhancement
**Status:** Amended
**Effort:** 0.5 days
**Requested:** 2026-05-01

---

## Judgement

**Verdict: APPROVED with amendments.**

The FR correctly diagnoses the root cause — `create_pr.sh` hardcodes `feat(chaplain):` which triggers CI gates the stubs cannot satisfy. The `docs:` title solution is minimal and sound. Five amendments:

### Amendment A1: `completed` state has the same infinite loop bug as `failed` had

The `completed` state has a bash action (`echo '✅ ...'`) but no `job_done` transition. When the action finishes, the engine re-enters it forever — identical to the `failed` loop fixed in the previous commit. Production `watcher-pipeline.yaml` has the same latent bug (post_merge.sh in `completed`).

**Fix**: Add `from: completed, to: stopped, event: job_done` transition. Same pattern as the `failed → stopped` fix. This is prerequisite for AC-5 — without it the pipeline can never terminate via the success path.

### Amendment A2: Preflight scope is wrong

The proposed preflight replaces the existing `preflight.sh` call with ruff checks. But `preflight.sh` does real work (validates CLI tools exist, checks git state). The ruff check should be **added** to the existing preflight action, not replace it. Either:
- Add ruff commands to `preflight.sh` itself (preferred — keeps all preflight logic in one place), or
- Add a second action in the preflight action list

### Amendment A3: Drop `changelog_gen` state — but also clean up events, transitions, and timeouts

AC-6 says "remove `changelog_gen` state" but doesn't mention the cascade: the `changelog_done` event, the `implementation_committed → changelog_gen` transition, the `changelog_gen → finalizing` transition, and the `changelog_gen → failed` error transition must all be removed. The `implementation_committed` event must route to `finalizing` directly. The existing FR-301 tests that validate `changelog_gen` existence must be updated (AC-8 covers this but should be explicit about which tests).

### Amendment A4: `run-integration-test.sh` must also stop the dispatcher

The current script runs the dispatcher indefinitely. After the pipeline completes (success or failure), the dispatcher returns to its idle loop and polls the inbox forever. The script needs to either:
- Send a `stop` event to the dispatcher after the pipeline exits, or
- Run the dispatcher with a `--once` mode (if supported), or
- Kill the dispatcher process after detecting pipeline termination in the log

Without this, the script never exits and AC-4 (exit code) is unreachable.

### Amendment A5: Branch name prefix should be `docs/` not `feat/`

`worktree_setup.sh` creates branch `feat/watcher2-<topic>`. With a `docs:` PR title, a `feat/` branch prefix is misleading. The integration pipeline should either:
- Override the branch name (add `--branch-prefix` to `worktree_setup.sh`), or
- Accept the mismatch as cosmetic and document it

**Recommendation**: Accept the mismatch. The branch name is not checked by any CI gate. Adding `--branch-prefix` is scope creep for a cosmetic concern.

### Scope Freeze

The following are in scope:
1. `--title` flag on `create_pr.sh` (AC-1)
2. Integration pipeline uses `docs(integration): smoke test` title (AC-2)
3. Ruff check added to `preflight.sh` (AC-3, amended per A2)
4. Exit code assertion in `run-integration-test.sh` (AC-4, amended per A4)
5. `completed → stopped` transition added (A1)
6. `changelog_gen` state fully removed with cascade cleanup (AC-6, amended per A3)
7. Tests updated (AC-7, AC-8)

The following are **out of scope**:
- Fixing the same `completed` loop bug in production `watcher-pipeline.yaml` (separate FR)
- Adding `--branch-prefix` to `worktree_setup.sh` (cosmetic, A5)
- Adding `--skip-ci` fallback flag (Alternative B — defer until needed)
- Any changes to CI gate definitions

**Authority granted. Enforce.**

## Summary

Make the FR-301 integration test pipeline produce artifacts that satisfy all CI gates, so the pipeline reaches `completed` instead of `failed`. Currently, the pipeline stubs create docs-only content that fails `commitlint` (missing FR-XXX in feat PR title). The fix is to use a `docs:` PR title prefix, bypassing all feat-specific gates.

## Value Statement

Watcher developers get a green integration test that proves the *entire* pipeline works end-to-end — including PR creation, CI pass, merge, and teardown — not just the failure path.

## Problem

FR-301 built the integration pipeline with bash stubs replacing LLM steps. The pipeline traverses all states correctly but always fails at `waiting_ci` because:

1. **`commitlint` fails**: `create_pr.sh` hardcodes `feat(chaplain):` as the PR title prefix. This triggers the `feat commits require FR-XXX` check. The integration pipeline has no FR reference to inject.

2. **Success path untested**: The pipeline reaches `failed → stopped` every run. States `merging`, `cleaning_up`, and `completed` have never been exercised. The test proves the failure path works but not the success path.

3. **Latent lint debt invisible**: Pre-commit on main runs on changed files only. The integration pipeline runs `--all-files` in the worktree (correct) but inherits latent ruff errors from main that were never caught by normal commits.

4. **No pass/fail exit code**: `run-integration-test.sh` exits 0 regardless of pipeline outcome. There is no assertion that the pipeline reached `completed`.

## Root Cause Analysis

The integration pipeline uses real `create_pr.sh` which assumes all PRs are `feat(chaplain):` changes. The integration test produces `docs:`-scoped changes (no code, no FR) that structurally cannot satisfy feat-specific CI gates. The design conflated "test the plumbing" with "produce a real feature PR."

### CI Gate Analysis

| Gate | Trigger | Integration Status | Fix Needed |
|------|---------|-------------------|------------|
| `commitlint` | All PRs | **FAILS** — `feat` title without FR-XXX | Use `docs:` or `chore:` title |
| `test` | All PRs | Passes — docs-only, no coverage impact | None |
| `conflict-check` | All PRs | Passes — clean generated files | None |
| `changelog-gate` | feat/fix PRs only | Passes (fragment exists) — but **skips** with docs title | None |
| `changelog-req-gate` | feat/fix PRs only | Passes (no `req:` field) — but **skips** with docs title | None |
| `diary-gate` | feat/fix PRs with FR-XXX | **Skips** — no FR in title | None |
| `demo-gate` | feat/fix PRs | **Skips** — no demo files touched | None |
| `security` | All PRs | Passes — no dep changes | None |

**Key insight**: Using a `docs:` PR title prefix makes 6/8 gates skip or pass trivially. Only `commitlint` (format check) and `test` (unit tests) remain active, and both pass.

## Proposed Solution

### 1. Add `--title` flag to `create_pr.sh`

Allow the caller to override the default `feat(chaplain):` title:

```bash
# Current (hardcoded):
PR_TITLE="feat(chaplain): ${WT_BRANCH#chaplain/}"

# New (with override):
PR_TITLE="${TITLE_OVERRIDE:-feat(chaplain): ${WT_BRANCH#chaplain/}}"
```

The integration pipeline passes `--title "docs(integration): smoke test"`.

### 2. Integration pipeline `creating_pr` state passes `--title`

```yaml
  creating_pr:
    - type: bash_context
      command: >-
        bash .chaplain/lib/watcher/create_pr.sh
        --branch {wt_branch}
        --dir {wt_dir}
        --title "docs(integration): smoke test"
      capture_keys: [pr_number, pr_url]
      success: pr_created
      error: error
```

### 3. Add ruff check to `preflight.sh` (A2)

Add ruff lint and format checks to the existing `preflight.sh` script — do not replace the existing preflight action. The script already validates CLI tools and git state; ruff checks belong alongside those. If ruff fails, preflight fails with a clear message before worktree creation.

```bash
# Added to preflight.sh (after existing checks):
log_info "Checking ruff lint..."
if ! ruff check . --quiet 2>/dev/null; then
    log_error "ruff check failed on main — fix before running integration test"
    exit 1
fi
if ! ruff format --check . --quiet 2>/dev/null; then
    log_error "ruff format failed on main — fix before running integration test"
    exit 1
fi
```

### 4. Exit code and dispatcher termination in `run-integration-test.sh` (A4)

The dispatcher runs indefinitely in its idle polling loop. After the pipeline terminates (success or failure), the script must kill the dispatcher process, then inspect the log to determine pass/fail.

```bash
# Run the dispatcher in background
statemachine .chaplain/config/integration-dispatcher.yaml \
  --actions-dir .chaplain/actions \
  --initial-context "{\"inbox_dir\":\"$INBOX\"}" \
  --debug &
DISPATCHER_PID=$!

# Wait for pipeline to complete (monitor log for terminal state)
FINAL_LOG=""
for i in $(seq 1 120); do
  sleep 5
  FINAL_LOG=$(ls -1t logs/fsm-integration-smoke-test-*.log 2>/dev/null | head -1)
  if [ -n "$FINAL_LOG" ] && grep -q "terminal state: stopped" "$FINAL_LOG" 2>/dev/null; then
    break
  fi
done

# Kill dispatcher
kill "$DISPATCHER_PID" 2>/dev/null || true
wait "$DISPATCHER_PID" 2>/dev/null || true

# Assert pipeline outcome
if [ -z "$FINAL_LOG" ]; then
  echo "❌ FAIL: No pipeline log found"
  exit 1
fi
if grep -q "completed --job_done--> stopped" "$FINAL_LOG"; then
  echo "✅ PASS: Pipeline reached completed"
  exit 0
else
  echo "❌ FAIL: Pipeline did not reach completed"
  tail -20 "$FINAL_LOG"
  exit 1
fi
```

### 5. Drop changelog fragment from integration stubs (A3)

With a `docs:` PR title, `changelog-gate` and `changelog-req-gate` skip entirely. The stub changelog fragment generation is unnecessary complexity. Full cascade removal:

- Remove `changelog_gen` from `states` list
- Remove `changelog_done` from `events`
- Remove transition `committing_implementation → changelog_gen` (event: `implementation_committed`)
- Remove transition `changelog_gen → finalizing` (event: `changelog_done`)
- Remove transition `changelog_gen → failed` (event: `error`)
- Add transition `committing_implementation → finalizing` (event: `implementation_committed`)
- Remove `changelog_gen` action block

### 6. Add `completed → stopped` transition (A1)

The `completed` state has a bash action (`echo '✅ ...'`) but no `job_done` transition. When the action finishes, the engine re-enters it forever — same infinite loop bug fixed in `failed` state. Add:

```yaml
  - from: completed
    to: stopped
    event: job_done
```

This is prerequisite for AC-5 — without it the pipeline cannot terminate via the success path.

## Acceptance Criteria

- [ ] AC-1: `create_pr.sh` accepts `--title` flag to override default PR title
- [ ] AC-2: Integration pipeline uses `docs(integration): smoke test` as PR title
- [ ] AC-3: Ruff check added to existing `preflight.sh` (not a replacement action) (A2)
- [ ] AC-4: `run-integration-test.sh` kills dispatcher, then exits non-zero when pipeline does not reach `completed` (A4)
- [ ] AC-5: Pipeline reaches `completed → stopped` on a clean main branch
- [ ] AC-6: `changelog_gen` state fully removed — state, event, all transitions, action block (A3)
- [ ] AC-7: `completed → stopped` transition on `job_done` added (A1)
- [ ] AC-8: Tests added validating pipeline structure changes
- [ ] AC-9: Existing FR-301 unit tests updated to reflect structural changes (changelog_gen removal)

## Alternatives Considered

### A: Make stubs produce real feat-quality artifacts
Rejected. Would require stubs to generate valid FR references, diary entries, and changelog fragments with correct REQ cross-references. This contradicts the "no LLM" constraint and adds fragile coupling to the capability registry.

### B: Skip `waiting_ci` entirely in integration mode
Partially rejected. Skipping CI validation defeats the purpose — we want to prove the full loop including merge. However, if CI proves unreliable (e.g., upstream CVE in `security` gate), a `--skip-ci` flag may be needed as a fallback.

### C: Use `chore:` instead of `docs:`
Either works. `docs:` is slightly more accurate since the stub produces `docs/watcher-integration.md` entries.

## Related

- FR-301: Watcher FSM Integration Test (parent — created the pipeline)
- FR-124: Watcher2 PR Reuse (create_pr.sh `--title` flag aligns with reuse pattern)
- CONF-300: `--no-verify` in integration stub commits
