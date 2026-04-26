# Feature Request: FR-287 watcher2 deduplication gate — skip already-completed FRs

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-26

## Summary

Add a pre-pipeline deduplication gate in watcher2 that detects when an inbox topic references an FR already merged in a prior PR, then skips the item instead of running a full duplicate cycle.

## Value Statement

Watcher2 operators avoid duplicate PR churn and save pipeline runtime by preventing re-processing of already-completed FR topics.

## Problem

Watcher2 can re-process old inbox items and execute the full Plan → Enforce pipeline even when the referenced FR is already merged. This caused a duplicate flow (`gh-208.md`) that consumed compute and produced a stale PR.

Current defenses are incomplete for this case:

1. `.chaplain/lib/watcher/inbox_sync.sh` deduplicates by file presence across inbox/processing/failed, not by completion state.
2. `.chaplain/lib/watcher/worktree_setup.sh` (FR-286) guards against merged **branch-name** reuse, but the stronger semantic check should happen earlier at topic intake.
3. `.chaplain/watcher2.sh` currently starts cycle work after moving an item to processing, without checking whether the FR in that topic was already completed.

## Objectives

1. Skip watcher2 cycles early when a topic references an FR already merged.
2. Consume skipped processing items so they are not retried on the next poll.
3. Preserve normal behavior when no FR reference exists or no merged PR is found.

## Constraints

- Scope is limited to watcher2 shell orchestration (`.chaplain/`); no YAMLGraph runtime changes.
- Keep deterministic branch naming and existing merged-branch guard from FR-286 unchanged.
- No hard failure if `gh` is unavailable or query fails; degrade gracefully with warning logs.
- Skip logic must be explicit in metrics (`outcome: "skipped"`).

## Research Findings

- `inbox_sync.sh` already performs stage-level dedup (`inbox`/`processing`/`failed`) but does not check completion state from merged PR history.
- `worktree_setup.sh` already uses dedicated skip-code control flow (`return 2`) for merged branch-collision handling; this pattern can be reused for the FR dedup gate.
- `watcher2.sh` already has a skip path that sets `CYCLE_OUTCOME="skipped"`, removes `TOPIC_FILE`, and writes metrics, so the new gate can slot into existing control-flow semantics.

## Proposed Solution

Implement a dedicated dedup boundary check before preflight/worktree setup.

### 1. Add a dedup guard helper in watcher shell libs

Create a focused helper (e.g., `.chaplain/lib/watcher/dedup_gate.sh`) that:

1. Extracts first FR token from the topic file (`FR-[0-9]+`).
2. If no FR token is present, returns success (continue pipeline).
3. Queries merged PR history by FR identifier:

```bash
gh pr list --state merged --search "FR-277" --json number,url,mergedAt,title \
  --jq '.[0] | select(.number != null)'
```

4. Returns a dedicated skip code when a merged PR is found and exposes merged PR metadata for logging.
5. Returns success with warning when `gh` is unavailable or query fails.

### 2. Wire guard into `.chaplain/watcher2.sh` before preflight

After moving topic to processing and initializing cycle variables:

1. Call the dedup guard with `TOPIC_FILE`.
2. On skip code:
   - set `CYCLE_OUTCOME="skipped"`,
   - log the matched merged PR,
   - remove `$TOPIC_FILE`,
   - write metrics,
   - continue polling loop without invoking `handle_failure`.
3. On non-skip, proceed with existing preflight/worktree pipeline.

### 3. Document behavior

Update `.chaplain/README.md` with:

- dedup gate purpose,
- FR extraction behavior,
- merged PR search pattern (`gh pr list --state merged --search "FR-XXX"`),
- graceful-degradation semantics.

## Acceptance Criteria

- [x] **AC-01:** Watcher2 checks topic content for an FR token (`FR-[0-9]+`) before preflight/worktree setup.
- [x] **AC-02:** When an FR token exists, watcher2 queries merged PR history using `gh pr list --state merged --search "FR-XXX"`.
- [x] **AC-03:** If a merged PR is found for the FR token, watcher2 treats the cycle as skip (not failure) and does not run plan/enforce steps.
- [x] **AC-04:** Skip path consumes the processing topic file (`rm "$TOPIC_FILE"`), preventing immediate re-pick.
- [x] **AC-05:** Skip path writes cycle metrics with `outcome` set to `skipped`.
- [x] **AC-06:** If no FR token is present in the topic, watcher2 behavior is unchanged (pipeline proceeds normally).
- [x] **AC-07:** If `gh` is unavailable or merged-query fails, watcher2 logs a warning and continues (no crash).
- [x] **AC-08:** Tests added in `tests/unit/test_fr287_watcher2_deduplication_gate.py` covering merged-hit skip, no-token pass-through, and graceful failure behavior.
- [x] **AC-09:** `.chaplain/README.md` documents the dedup gate and merged-PR search contract.

## Alternatives Considered

1. **Rely only on branch-collision guard (FR-286):** Rejected. It is defense-in-depth, but dedup by FR completion should happen earlier and semantically at topic intake.
2. **Randomized branch names:** Rejected. Avoids collisions but does not prevent duplicate execution for already-completed FRs.
3. **Manual inbox hygiene only:** Rejected. Operator-driven cleanup is not reliable for daemonized automation.

## Related

- Issue #232: watcher2 deduplication gate — skip already-completed FRs
- Issue #233: merged-branch collision follow-up
- PR #211 (merged FR-277) and PR #231 (duplicate)
- `.chaplain/watcher2.sh`
- `.chaplain/lib/watcher/inbox_sync.sh`
- `.chaplain/lib/watcher/worktree_setup.sh`
- FR-275 watcher2 PR reuse
- FR-286 merged-branch collision guard

## Research Brief

### Competitive Landscape

- **LangGraph**: durable execution guidance emphasizes idempotent side effects and idempotency keys to avoid duplicate effects on resume, but it does not provide GitHub PR/FR completion dedup out of the box.
  <https://docs.langchain.com/oss/python/langgraph/durable-execution>
- **CrewAI Flows**: provides event-driven flows with persistent state IDs and control flow, but no native "already merged work item" gate tied to GitHub PR history.
  <https://docs.crewai.com/en/concepts/flows>
- **AutoGen Core**: focuses on resilient actor/event-driven multi-agent orchestration; dedup semantics against external SCM history are left to application logic.
  <https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html>
- **Google ADK**: workflow agents are deterministic orchestrators (sequential/parallel/loop), but PR-history dedup is still an integration concern outside the framework primitive set.
  <https://google.github.io/adk-docs/agents/workflow-agents/>
- **OpenAI Agents SDK**: sessions/sandbox support memory and resumable workspaces, but no built-in GitHub merged-PR dedup primitive.
  <https://openai.github.io/openai-agents-python/sessions/>
  <https://openai.github.io/openai-agents-python/sandbox_agents/>
- **GitHub Actions**: concurrency groups prevent overlapping runs, but do not answer "has this FR already been merged before?" for watcher2 topic re-ingestion.
  <https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency>
- **Build vs document**: documenting idempotency guidance alone is cheaper short-term, but it does not close this concrete watcher2 control-flow gap; a small guard in code is the lower-risk fix.

### Existing Abstractions

- Stage-level dedup already exists in `.chaplain/lib/watcher/inbox_sync.sh` (`inbox`/`processing`/`failed` presence checks), but it does not inspect FR completion.
- Open-PR reuse exists in `.chaplain/lib/watcher/create_pr.sh` (`gh pr list --state open --head "$WT_BRANCH"`), but this is branch/open-state scoped.
- Merged-branch collision guard exists in `.chaplain/lib/watcher/worktree_setup.sh` (`gh pr list --state merged --head "$WT_BRANCH"` with skip `return 2`) as defense-in-depth.
- Skip control flow and metrics are already wired in `.chaplain/watcher2.sh` (`CYCLE_OUTCOME="skipped"`, `rm "$TOPIC_FILE"`, `write_cycle_metrics`).
- Documentation and executable proofs already exist:
  - `.chaplain/README.md` (merged-branch guard contract)
  - `tests/unit/test_fr286_watcher2_merged_branch_collision_guard.py`
  - `examples/demos/watcher2-merged-branch-collision-guard/graph.yaml`
- **Gap confirmed**: no current watcher lib/orchestrator query uses `gh pr list --state merged --search "FR-XXX"` for FR-token completion dedup.

### Diary Precedents

- `docs/diary/2026-04-25-reflection-fr-284-ci-remediation-crash.md`: **downstream_fix** lesson — under `set -e`, unguarded `gh` calls are crash points and must be boundary-guarded.
- `docs/diary/2026-04-25-reflection-fr-285-forensic-failure-diary.md`: normalize at a single boundary (`handle_failure`) instead of scattering fixes downstream.
- `docs/diary/2026-04-25-reflection-fr-280-watcher2-red-verification-timestamp-fix.md`: **partial_remediation** risk — assert intent-level behavior, not incidental syntax.
- `docs/diary/2026-04-23-reflection-fr-286-watcher2-merged-branch-collision-guard.md`: **false_duplicate** warning — boundary semantics can differ despite familiar syntax.
- `docs/diary/2026-04-20-reflection-fr-258-automate-post-merge-finalization.md`: shared watcher library extraction pattern reduces drift between automation paths.

### Usage Evidence

- Existing graphs using related abstractions: **0** (no public `graphs/` or `examples/` graph currently implements FR-token merged-history dedup).
- Real-world use cases beyond the proposal:
  - `.chaplain/watcher2.sh` production daemon path
  - watcher2 demos (5):
    `examples/demos/watcher2-changelog-gen/graph.yaml`
    `examples/demos/watcher2-ci-remediation/graph.yaml`
    `examples/demos/watcher2-remediation/graph.yaml`
    `examples/demos/watcher2-red-verification/graph.yaml`
    `examples/demos/watcher2-merged-branch-collision-guard/graph.yaml`
  - internal watcher orchestration graphs (2):
    `.chaplain/graphs/watcher-diary/graph.yaml`
    `.chaplain/graphs/watcher-forensic/graph.yaml`

### Classification Signal

- Abstraction level: **integration**
- Recommended approach: **build**
- Key risk: naive FR-token extraction can cause false-positive skips when a topic references historical FRs contextually rather than declaring already-completed intent.

## Judge Verdict

**Verdict: APPROVE**

### Evaluation

1. **Scope clear and minimal:** Yes. The FR is tightly scoped to one bug class: re-processing already-completed FR topics in watcher2.
2. **Contradictions/ambiguities:** No blocking contradictions. Main ambiguity (false-positive skips from incidental FR mentions) is identified in the research brief and can be handled within implementation constraints.
3. **Acceptance criteria measurable:** Yes. AC-01..AC-09 are testable with structural/behavioral checks against watcher2 shell libs and docs.
4. **Implementation feasibility:** Yes. The proposal fits existing watcher2 shell-lib architecture and mirrors established skip-code patterns (FR-286).
5. **Architecture alignment:** Yes. Boundary check in watcher layer + orchestrator-owned skip/continue flow is consistent with current `.chaplain/lib/watcher/*` split.
6. **Single responsibility:** Yes. This FR focuses on completion-state dedup only; it does not bundle unrelated pipeline refactors.
7. **Classification (judge taxonomy):** **Contrib/example** — this is an infrastructure integration fix with limited watcher2-specific use cases, not a YAMLGraph framework primitive.
8. **Acceptance tests validity:** `tests/unit/test_fr287_watcher2_deduplication_gate.py` compiles and fails for missing dedup implementation/documentation (not import/fixture failures), so the FR is sufficiently specified for enforcement.

### Scope Freeze

Implementation authority is granted for this FR with frozen scope:

- Add FR-token dedup guard in watcher shell library (pre-preflight boundary check).
- Query merged PR history with `gh pr list --state merged --search "FR-XXX"` when token exists.
- Route merged-hit path to explicit skip control flow in `watcher2.sh` (no failure handler path).
- Consume skipped processing topic and emit skipped cycle metrics.
- Preserve pass-through behavior when no FR token exists.
- Degrade gracefully when `gh` is unavailable/query fails.
- Update `.chaplain/README.md` for dedup-gate contract and merged-search semantics.
- Satisfy AC-01..AC-09 without expanding to broader watcher2 refactors.
