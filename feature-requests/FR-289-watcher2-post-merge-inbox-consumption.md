# Feature Request: FR-289 watcher2 post-merge inbox consumption for matching FR items

**Priority:** HIGH  
**Type:** Bug  
**Status:** Implemented  
**Effort:** 0.5 days  
**Requested:** 2026-04-26

## Summary

Extend watcher2 post-merge cleanup to consume stale inbox items that reference the same FR as the just-merged work, so orphaned duplicates are not re-processed later.

## Value Statement

Watcher2 operators avoid duplicate pipeline cycles and ghost follow-up PRs because related inbox items are consumed immediately after a successful merge.

## Problem

`post_merge` currently closes the originating GitHub issue (`gh-*.md`) but does not remove other inbox files that reference the same completed FR.

This leaves stale files in `.chaplain/inbox/` that can be picked up in later cycles. Even with FR-287 dedup at processing time, these leftovers still create avoidable poll churn and unnecessary skip cycles.

Observed context from topic:

1. A topic referencing `FR-277` remained in inbox after successful merge.
2. The leftover item survived restarts and was re-processed later.

## Objectives

1. After successful merge, identify the merged FR token (`FR-XXX`) for the completed work item.
2. Scan `.chaplain/inbox/` for files referencing that same token.
3. Consume matched inbox files into a completed queue (`.chaplain/done/`) so they are not re-picked.
4. Preserve existing watcher2 behavior when no FR token can be resolved.

## Constraints

- Scope is limited to watcher2 shell infrastructure (`.chaplain/lib/watcher/post_merge.sh`, `.chaplain/README.md`, and tests).
- No changes to YAMLGraph runtime, node types, or CLI behavior.
- Keep existing success-path ownership: orchestrator still removes `TOPIC_FILE`; post-merge consumes only *other* inbox matches.
- Use existing shell + `gh` tooling only; no new dependencies.
- Post-merge cleanup failures should be surfaced via logs but must not undo a successful merge.

## Proposed Solution

Implement FR-token-based inbox consumption in `post_merge.sh`.

### 1. Resolve merged FR token in post-merge boundary

Add a small helper in `post_merge.sh` to resolve the first `FR-[0-9]+` token using:

1. `PR_NUMBER` title lookup (`gh pr view "$PR_NUMBER" --json title --jq '.title'`) when available.
2. Fallback to already-derived `PR_TITLE`.
3. Optional final fallback to current `TOPIC_FILE` content.

If no FR token is found, log and exit cleanup path without error.

### 2. Consume matching inbox files

After successful merge and issue-close handling:

1. Scan `.chaplain/inbox/*.md` for the resolved token.
2. Create `.chaplain/done/` if missing.
3. Move matching files from inbox to done (leave non-matching files untouched).
4. Log consumed filenames and total count.

If a destination filename already exists in `.chaplain/done/`, append a deterministic suffix (timestamp) to avoid overwrite.

### 3. Keep behavior explicit in docs

Update `.chaplain/README.md` to document:

- post-merge FR-token extraction source order,
- inbox scan behavior,
- `.chaplain/done/` role as consumed-completed queue.

## Acceptance Criteria

- [x] **AC-01:** `post_merge.sh` resolves an `FR-[0-9]+` token from merged work context (PR metadata and/or existing watcher variables).
- [x] **AC-02:** On successful token resolution, post-merge scans `.chaplain/inbox/` for markdown files containing that token.
- [x] **AC-03:** Matching inbox files are moved to `.chaplain/done/` (not left in inbox), and non-matching files remain unchanged.
- [x] **AC-04:** `.chaplain/done/` is created automatically when absent.
- [x] **AC-05:** Destination collision is handled safely (no silent overwrite of existing done files).
- [x] **AC-06:** If no FR token is resolved, watcher2 continues normally and no inbox files are moved.
- [x] **AC-07:** Cleanup emits explicit logs for token resolution outcome and number of consumed files.
- [x] **AC-08:** Tests added in `tests/unit/test_fr289_watcher2_post_merge_inbox_consumption.py` covering token resolution path, inbox match consumption path, no-token no-op path, and done-directory handling.
- [x] **AC-09:** `.chaplain/README.md` documents post-merge inbox consumption and `.chaplain/done/` semantics.

## Implementation Notes

- Added `resolve_post_merge_fr_token()` in `.chaplain/lib/watcher/post_merge.sh` with source order: `PR_NUMBER` (`gh pr view`) → `PR_TITLE` → `TOPIC_FILE`.
- Added `consume_matching_inbox_items()` to scan `.chaplain/inbox/*.md`, create `.chaplain/done/`, move matching files, and suffix collisions with `-$(date +%Y%m%d%H%M%S)`.
- Preserved no-token path as explicit logged no-op (`return 0`) so successful merges are never undone by cleanup.
- Updated `.chaplain/README.md` to document post-merge token resolution, inbox scan/move behavior, and `.chaplain/done/` semantics.

## Alternatives Considered

1. **Rely only on FR-287 processing-time dedup skip:** Rejected. It prevents duplicate execution but still allows stale inbox accumulation and repeated skip churn.
2. **Delete matching inbox files immediately (no done queue):** Rejected for this FR. Hard deletion removes audit visibility; moving to `.chaplain/done/` preserves traceability.
3. **Only close source GitHub issue and do no local cleanup:** Rejected. Duplicate local inbox entries can still survive and trigger later cycles.

## Related

- Topic: `.chaplain/processing/gh-234.md`
- `.chaplain/lib/watcher/post_merge.sh`
- `.chaplain/watcher2.sh`
- `.chaplain/lib/watcher/inbox_sync.sh` (FR-243 remote inbox import)
- `.chaplain/lib/watcher/dedup_gate.sh` (FR-287 processing-time dedup)
- `feature-requests/FR-287-watcher2-deduplication-gate.md`
- `feature-requests/FR-243-github-issues-remote-inbox.md`

## Research Brief

### Competitive Landscape

- **LangGraph** emphasizes durable execution + idempotent side effects (`tasks`, idempotency keys), which is conceptually related but does not provide GitHub inbox-item cleanup primitives.
  - <https://docs.langchain.com/oss/python/langgraph/durable-execution>
- **CrewAI Flows** provides stateful event-driven orchestration, but no built-in “consume completed work item from external inbox” behavior.
  - <https://docs.crewai.com/en/concepts/flows>
- **AutoGen Core** provides resilient event-driven multi-agent runtime, but leaves queue dedup/cleanup policies to application code.
  - <https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html>
- **Google ADK Workflow Agents** provides deterministic sequential/parallel/loop orchestration, not SCM-aware post-merge queue cleanup.
  - <https://google.github.io/adk-docs/agents/workflow-agents/>
- **OpenAI Agents SDK (Sessions)** provides conversation/run memory and resume semantics, not repository inbox lifecycle management.
  - <https://openai.github.io/openai-agents-python/sessions/>
- **GitHub Actions concurrency** controls overlapping runs per concurrency group, but does not solve stale local inbox artifacts tied to merged FRs.
  - <https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency>
- **Build vs document:** documenting generic idempotency guidance would be cheaper short-term, but it does not close the concrete watcher2 gap (`post_merge` not consuming related inbox items). This needs a small integration fix in watcher shell libs.

### Existing Abstractions

- `.chaplain/lib/watcher/post_merge.sh` currently closes only the originating `gh-*.md` issue; no scan of `.chaplain/inbox/` for related FR tokens.
- `.chaplain/lib/watcher/dedup_gate.sh` already extracts `FR-[0-9]+` and checks merged PR history at **processing time**.
- `.chaplain/lib/watcher/inbox_sync.sh` already deduplicates by stage presence (`inbox`/`processing`/`failed`) when importing remote issues.
- `.chaplain/watcher2.sh` already models queue lifecycle across `.chaplain/inbox`, `.chaplain/processing`, and `.chaplain/failed`; there is no completed queue (`.chaplain/done`) today.
- `.chaplain/lib/watcher/metrics.sh` already emits outcome metrics, so post-merge cleanup changes can remain localized without new telemetry infrastructure.

### Diary Precedents

- `docs/diary/2026-04-20-reflection-fr-258-automate-post-merge-finalization.md`
  - Trap: `downstream_fix`; cure was boundary normalization via shared shell lib extraction.
- `docs/diary/2026-04-25-reflection-fr-285-forensic-failure-diary.md`
  - Reinforces: centralize behavior at a single boundary (`handle_failure` in that FR), not scattered callsites.
- `docs/diary/2026-04-25-reflection-fr-284-ci-remediation-crash.md`
  - External `gh` calls under `set -e` are crash-prone; guard and log explicitly.
- `docs/diary/2026-04-23-reflection-fr-287-watcher2-deduplication-gate.md`
  - Prior dedup work confirms FR-token checks belong at explicit pipeline boundaries.
- `docs/diary/2026-04-20-reflection-fr-243-github-issues-remote-inbox.md`
  - Remote inbox widened intake boundary; this FR is the complementary cleanup boundary on exit.

### Usage Evidence

- Existing graphs using related abstractions: **0**
  - No YAML graph under `graphs/` or `examples/` references `post_merge`, `.chaplain/done`, or this post-merge inbox-consumption behavior.
- Real-world use cases beyond the proposal:
  - `.chaplain/watcher2.sh` (single orchestrator callsite for `post_merge`)
  - `.chaplain/lib/watcher/inbox_sync.sh` (remote inbox ingestion lifecycle)
  - `.chaplain/lib/watcher/dedup_gate.sh` (processing-time dedup boundary)
  - Watcher-focused demos in `examples/demos/watcher2-*/graph.yaml` (**7** demo graphs) and internal watcher graphs in `.chaplain/graphs/watcher-*/graph.yaml` (**2**), indicating active watcher2 operational surface even though none directly implement post-merge inbox consumption.

### Classification Signal

- Abstraction level: **integration**
- Recommended approach: **build**
- Key risk: FR-token matching may over-consume unrelated inbox files that merely mention the same FR in background context unless token extraction and matching rules are tightly scoped and logged.

## Judge Verdict

**Verdict: APPROVE**

### Evaluation

1. **Scope clear and minimal:** Yes. The FR targets one bug class: stale inbox items left after successful merge.
2. **Contradictions or ambiguities:** No blocking contradictions. The only notable risk (over-matching by FR token) is explicitly captured and can be handled within this FR by scoped matching and logs.
3. **Acceptance criteria measurable:** Yes. AC-01..AC-09 are concrete and testable against shell script structure/behavior and README documentation.
4. **Implementation approach feasible:** Yes. The change is localized to `post_merge.sh` + docs and reuses existing watcher shell patterns.
5. **Architecture alignment:** Yes. The fix stays in watcher2 shell orchestration (`.chaplain/lib/watcher/*`) with no YAMLGraph runtime surface change.
6. **Single responsibility:** Yes. This FR does not bundle unrelated pipeline refactors.
7. **Classification (judge taxonomy):** **Contrib/example** — this is watcher2 integration hardening with limited use cases, not a framework primitive.
8. **Acceptance tests validity:** `tests/unit/test_fr289_watcher2_post_merge_inbox_consumption.py` compiles and fails for missing implementation/doc behavior (8 failed, 1 passed), not for import/fixture errors.

### Scope Freeze

Implementation authority is granted for this FR with frozen scope:

- Add FR-token resolution in `post_merge.sh` from merged work context (`PR_NUMBER`/`PR_TITLE` with topic fallback).
- Scan `.chaplain/inbox/*.md` for token matches after successful merge.
- Move matching files to `.chaplain/done/`, creating the directory when needed.
- Preserve non-matching inbox files.
- Handle destination filename collisions without overwrite.
- Keep no-token behavior as explicit no-op with logs.
- Emit explicit logs for token resolution and consumed file counts.
- Update `.chaplain/README.md` to document post-merge inbox consumption and `.chaplain/done/` semantics.
- Satisfy AC-01 through AC-09 without expanding into unrelated watcher2 refactors.
