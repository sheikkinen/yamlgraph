# Feature Request: FR-286 watcher2 merged-branch collision guard

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-26

## Summary

Add a pre-worktree guard in watcher2 that skips processing when the deterministic branch name for a topic already has a merged PR, preventing ghost duplicate PRs from branch-name reuse.

## Value Statement

Watcher2 operators avoid duplicate PR churn and wasted pipeline runtime when previously completed inbox items are accidentally re-processed.

## Problem

Watcher2 currently derives branch names deterministically from inbox filenames in `.chaplain/lib/watcher/worktree_setup.sh`:

- `WT_BRANCH="feat/watcher2-${topic_basename}"`

If an item like `gh-208.md` is processed again after its original branch was merged and deleted, watcher2 recreates the same branch name and runs the full pipeline again. This produced a stale duplicate:

- PR #211 (merged) and PR #231 (stale duplicate) both used `feat/watcher2-gh-208`

Why this happens in the current architecture:

1. `worktree_setup.sh` has no historical merged-branch check before `git worktree add`.
2. `create_pr.sh` (FR-275) only reuses **open** PRs; it does not prevent creating new PRs on recycled branch names.
3. Remote inbox retries are intentionally possible via relabeling (`chaplain`) from FR-243, so re-processing can occur unless explicitly gated.

## Objectives

1. Prevent branch-name collision duplicates before worktree creation.
2. Keep deterministic branch naming (`feat/watcher2-{topic}`) for traceability and existing tooling.
3. Keep this fix scoped to watcher2 shell infrastructure (no YAMLGraph core changes).

## Constraints

- Do not add random/timestamp branch suffixes in this FR.
- Do not change `create_pr.sh` open-PR reuse behavior.
- Follow existing watcher2 architecture: shell lib does the boundary check, orchestrator owns skip/continue control flow.
- Keep graceful degradation if `gh` is unavailable or the merged-query fails.
- Maintain compatibility with Issue #232 as primary dedup strategy; this FR is defense-in-depth.

## Proposed Solution

Implement Option B (merged-branch guard) as defense-in-depth while Issue #232 dedup gate remains the primary prevention layer.

### 1. Add merged-branch guard to `worktree_setup.sh`

After deriving `WT_BRANCH`, query merged PR history for that head branch:

```bash
existing_merged_pr=$(gh pr list \
  --state merged \
  --head "$WT_BRANCH" \
  --json number,url,mergedAt \
  --jq '.[0] | select(.number != null)' 2>/dev/null || true)
```

If found:
- log skip with PR URL/number,
- set skip metadata variables (for orchestrator/metrics),
- return a dedicated non-crash skip code (for example `2`).

If query fails (auth/network/CLI unavailable):
- log warning,
- continue with existing behavior (do not hard-fail cycle).

### 2. Handle skip code in `.chaplain/watcher2.sh`

When `worktree_setup` returns the collision skip code:
- treat as **skip**, not failure,
- remove the processing topic file to prevent immediate re-pick,
- write cycle metrics with explicit skip outcome,
- continue main loop without invoking `handle_failure`.

### 3. Keep branch format unchanged

No branch suffixing in this FR. Deterministic naming remains:
- `feat/watcher2-{topic_basename}`

This preserves existing assumptions in docs, scripts, and FR traceability while blocking known collision scenarios.

## Acceptance Criteria

- [x] **AC-01:** `worktree_setup.sh` checks for merged PR history on the derived `WT_BRANCH` before `git worktree add`.
- [x] **AC-02:** If a merged PR exists for `WT_BRANCH`, `worktree_setup.sh` returns a dedicated skip code and logs the merged PR reference.
- [x] **AC-03:** `watcher2.sh` handles that skip code as non-failure (no `handle_failure` invocation).
- [x] **AC-04:** On skip, the processing topic file is consumed (removed from `.chaplain/processing`) so it is not retried in the next poll.
- [x] **AC-05:** Metrics record an explicit skip outcome for this path.
- [x] **AC-06:** When no merged PR exists, watcher2 behavior is unchanged (worktree creation proceeds normally).
- [x] **AC-07:** If `gh` is unavailable/query fails, guard degrades gracefully and does not crash watcher2.
- [x] **AC-08:** Tests added for merged-branch detection, skip control flow, and unchanged happy path.
- [x] **AC-09:** `.chaplain/README.md` updated to document the merged-branch collision guard.

## Alternatives Considered

1. **Option A: Timestamp/hash suffix branch names (`feat/watcher2-gh-208-<suffix>`)**
   Rejected for this FR. It avoids collisions but reduces traceability, complicates cleanup/debugging, and hides the missing dedup boundary instead of guarding it.

2. **Option C only: Rely solely on Issue #232 dedup gate**
   Rejected as sole mitigation. It should remain the primary gate, but this branch-level check is needed as defense-in-depth if dedup logic regresses or misses edge cases.

3. **Remote branch-only detection via `git branch -r --list`**
   Rejected. Remote branch existence is weaker than merged PR history and can be absent after normal branch deletion.

## Related

- Issue #233: watcher2 branch name collision with previously merged PRs
- Issue #232: watcher2 deduplication gate — skip already-completed FRs
- PR #211 (merged) and PR #231 (stale duplicate)
- `.chaplain/lib/watcher/worktree_setup.sh`
- `.chaplain/watcher2.sh`
- `.chaplain/lib/watcher/create_pr.sh` (FR-275 open-PR reuse behavior)
- `.chaplain/lib/watcher/inbox_sync.sh` (FR-243 remote inbox retry semantics)

## Research Brief

### Competitive Landscape

- **LangGraph** focuses on durable execution/checkpoint replay and explicitly recommends idempotent side effects and idempotency keys on resume; it does not provide Git branch/PR collision handling primitives.
  Source: <https://docs.langchain.com/oss/python/langgraph/durable-execution>
- **CrewAI Flows** provides flow state IDs plus persistence/resume (`@persist`) for workflow continuity, but no built-in branch naming or merged-PR dedup controls.
  Source: <https://docs.crewai.com/en/concepts/flows>
- **AutoGen Core** is an event-driven agent runtime (resilient/distributed), with orchestration primitives rather than Git workflow guards.
  Source: <https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html>
- **Google ADK** positions itself around context management, failure handling, and task resume, but not repository branch lifecycle deduplication.
  Source: <https://google.github.io/adk-docs/>
- **OpenAI Agents SDK** offers session memory and resumable sandbox sessions, but not branch/PR identity collision protection.
  Sources: <https://openai.github.io/openai-agents-python/sessions/>, <https://openai.github.io/openai-agents-python/sandbox_agents/>
- **GitHub Actions** supports concurrency groups to suppress duplicate runs, but this addresses run overlap, not recycled branch-name collisions against merged PR history.
  Source: <https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency>
- **Renovate** is the closest precedent: it exposes explicit branch naming controls and `recreateWhen` (formerly `recreateClosed`) to control whether closed PRs are re-created. This validates adding first-class anti-duplication policy around branch/PR identity.
  Source: <https://docs.renovatebot.com/configuration-options/>

**Build vs document:** documentation alone is not sufficient here. The defect is an active watcher2 control-flow gap at worktree creation time; a small guard in code is cheaper and safer than relying on operator discipline.

### Existing Abstractions

- Deterministic branch derivation already exists in `.chaplain/lib/watcher/worktree_setup.sh` (`WT_BRANCH="feat/watcher2-${topic_basename}"`), but there is no merged-history guard before `git worktree add`.
- PR reuse exists in `.chaplain/lib/watcher/create_pr.sh`, but it only checks `gh pr list --state open --head "$WT_BRANCH"` (open PRs), not merged history.
- Inbox-level dedup exists in `.chaplain/lib/watcher/inbox_sync.sh` (skip if file already in inbox/processing/failed), but it is file-stage dedup, not branch-history dedup.
- Outcome telemetry exists in `.chaplain/lib/watcher/metrics.sh` (`outcome` field), so adding an explicit skip outcome fits existing abstraction.
- Documentation currently codifies deterministic branch naming in `.chaplain/README.md` (worktree setup section), so this FR should update that contract.

### Diary Precedents

- `docs/diary/2026-04-25-reflection-fr-284-ci-remediation-crash.md` — warns against **downstream_fix**; external `gh` calls under `set -e` must be guarded at the boundary.
- `docs/diary/2026-04-25-reflection-fr-285-forensic-failure-diary.md` — reinforces boundary centralization (“normalize at the entry boundary”) instead of scattered symptom patches.
- `docs/diary/2026-04-25-reflection-fr-280-watcher2-red-verification-timestamp-fix.md` — highlights **partial_remediation** and fragile infra tests; intent-level checks preferred over incidental syntax coupling.
- `docs/diary/2026-04-18-genesis.md` — prior dedup omission in automation infrastructure caused repeated duplicate proposals, validating defense-in-depth dedup gates.

### Usage Evidence

- Existing graphs using related abstractions: **0** (no YAML graphs/examples invoke `worktree_setup`/`create_pr` abstractions directly; this is shell orchestration infrastructure).
- Real-world use cases beyond the proposal:
  - Production watcher daemon: `.chaplain/watcher2.sh`
  - Existing watcher2 demos: `examples/demos/watcher2-ci-remediation`, `examples/demos/watcher2-remediation`, `examples/demos/watcher2-red-verification`, `examples/demos/watcher2-changelog-gen`

### Classification Signal

- Abstraction level: **integration**
- Recommended approach: **build**
- Key risk: false-positive skips if a branch name is intentionally reused for a genuinely new task with the same topic basename, so skip criteria must be tightly tied to merged-PR evidence and logged clearly.

## Judge Verdict

**Verdict: APPROVE**

### Evaluation

1. **Scope clear and minimal:** Yes. The FR is focused on one defect class: recycled deterministic branch names producing ghost duplicate PRs.
2. **Contradictions/ambiguities:** No blocking contradictions. The skip-path contract is coherent across `worktree_setup.sh`, `watcher2.sh`, metrics, and docs.
3. **Acceptance criteria measurable:** Yes. AC-01..AC-09 are structurally testable against shell scripts and docs.
4. **Implementation feasibility:** Yes. The approach is incremental and fits current watcher2 control flow.
5. **Architecture alignment:** Yes. Boundary guard in `worktree_setup` plus orchestrator skip handling follows existing watcher2 shell-lib/orchestrator split.
6. **Single responsibility:** Yes. This FR does not bundle unrelated feature work; docs and tests are directly coupled to the same bug fix.
7. **Classification (per judge taxonomy):** **Contrib/example** — this is a targeted infrastructure hardening with a concrete watcher2 use case, not a framework primitive.
8. **Acceptance tests validity:** `tests/unit/test_fr286_watcher2_merged_branch_collision_guard.py` compiles and fails for missing implementation behavior (not import/fixture failures), so the FR is sufficiently specified for implementation.

### Scope Freeze

Implementation authority is granted for this FR with the following frozen scope:

- Add merged-PR collision detection before worktree creation.
- Route collision to explicit skip control flow in watcher2 (no failure handler path).
- Consume skipped processing topic and emit explicit skip metrics.
- Update `.chaplain/README.md` for the new guard behavior.
- Satisfy AC-01..AC-09 and no broader watcher2 refactors.
