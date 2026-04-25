# Feature Request: FR-277 Watcher2 Baseline Checkpointing

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 4 days
**Requested:** 2026-04-25
**Judged:** 2026-04-25

## Summary

Add baseline checkpointing for watcher2 so stable doctrine/context inputs are precomputed once and reused across runs via imported state, with deterministic hash-based invalidation.

## Value Statement

Watcher2 operators get lower token spend and more stable plan quality across runs by reusing a verified baseline context instead of rescanning unchanged corpus each cycle.

## Problem

FR-276 Phase 1 (Anthropic prompt caching) reduces repeated token cost within a single run window, but watcher2 still repeatedly rescans mostly stable sources across runs:

- Scripture and instruction corpus
- `ARCHITECTURE.md` and `CLAUDE.md`
- Diary index slices used by watcher2
- Active FR digest inputs used by watcher2

Without cross-run baseline reuse:
- startup of each run redoes the same expensive preparation,
- run-to-run variability increases because context assembly is recomputed ad hoc,
- operator cost remains high even when source material is unchanged.

## Proposed Solution

### 1. Baseline builder contract

Create a dedicated baseline builder entrypoint:

```bash
# .chaplain/lib/watcher/build_baseline.sh
yamlgraph graph run .chaplain/graphs/baseline/graph.yaml \
  --export-state .chaplain/baseline/${BASELINE_ID}.json
```

`BASELINE_ID` is deterministic from a content hash over a locked input manifest.

### 2. Input manifest and hash identity

Define a manifest file listing tracked baseline sources (patterns + mode):

```yaml
# .chaplain/baseline/manifest.yaml
manifest_version: 1
sources:
  - pattern: .github/copilot-instructions.md
    mode: verbatim
  - pattern: ARCHITECTURE.md
    mode: verbatim
  - pattern: CLAUDE.md
    mode: verbatim
  - pattern: .pre-commit-config.yaml
    mode: verbatim
  - pattern: scripts/req_coverage.py
    mode: verbatim
  - pattern: docs/diary/index.md
    mode: summarized
  - pattern: feature-requests/*.md
    mode: summarized
exclude:
  - feature-requests/TEMPLATE.md
  - feature-requests/REJECTED-*.md
```

Hash algorithm:
- Normalize line endings to `\n`.
- Expand patterns in sorted path order.
- Concatenate `path + sha256(content)` in resolved order.
- `BASELINE_ID = sha256(concatenated_entries + manifest_version)`.

Coverage boundary:
- Baseline is a stable-subset cache, not the full watcher2 context.
- Non-baseline sources continue to be loaded directly by runtime steps.

### 3. Summary determinism strategy

Choose Option B.

- Summary cache key: `sha256(source_content + summary_prompt_version + summary_model)`.
- For unchanged summary key, reuse cached summary text instead of regenerating.
- Summarized outputs are stored alongside metadata (`summary_model`, `summary_prompt_version`, `summary_key`).
- `BASELINE_ID` remains source-manifest deterministic; summary cache key guarantees reproducible summarized payload reuse.

### 4. Baseline builder graph skeleton

Define explicit graph stages in `.chaplain/graphs/baseline/graph.yaml`:

- `load_manifest`: read and validate manifest schema.
- `expand_sources`: resolve globs + excludes to concrete files.
- `read_sources`: load file content and compute per-source hashes.
- `resolve_summaries`: for `mode: summarized`, reuse by `summary_key` or generate then persist.
- `compute_baseline_id`: compute deterministic `BASELINE_ID`.
- `assemble_baseline_state`: build namespaced `baseline_*` state fields.
- `emit_artifact`: write export state consumed by watcher2.

### 5. Baseline state schema

Baseline export contains at minimum:

- `baseline_id: str`
- `baseline_manifest_version: str`
- `baseline_built_at: str` (ISO8601)
- `baseline_sources: list[dict]` with path + content hash
- `baseline_context_verbatim: dict[str, str]`
- `baseline_context_summaries: dict[str, str]`
- `baseline_summary_meta: dict[str, dict]` (model, prompt_version, summary_key)
- `baseline_warnings: list[str]`

### 6. Rebuild, pointer, and retention logic

- Compute current `BASELINE_ID` before watcher2 plan step.
- If `.chaplain/baseline/${BASELINE_ID}.json` exists, reuse it.
- Else build and export new baseline.
- Update `.chaplain/baseline/latest.json` as a symlink to the active baseline artifact.
- On successful rebuild, keep the latest 5 baseline artifacts and delete older ones.

### 7. Watcher2 import integration

Before plan/research:

```bash
yamlgraph graph run step-plan.yaml \
  --import-state .chaplain/baseline/latest.json \
  --var proposal="@$INBOX_FILE"
```

Import must be additive only:
- baseline keys are namespaced under `baseline_*`,
- proposal-specific keys continue to be computed per run,
- no silent overwrite of non-baseline state keys.

## Acceptance Criteria

- [ ] Manifest schema exists with glob support (`pattern`), explicit `mode`, and `exclude` support
- [ ] Integration scope remains watcher2-only (`.chaplain/` + watcher2 scripts), with no yamlgraph core changes
- [ ] `BASELINE_ID` is deterministic: same sources and manifest version produce the same hash (tested)
- [ ] Unchanged sources do not trigger rebuild (tested)
- [ ] Changed source produces new `BASELINE_ID` and new artifact (tested)
- [ ] Baseline builder graph defines concrete nodes for read, summary-resolution, hash, assemble, and export
- [ ] Summary determinism strategy is implemented with summary cache keys and reuse
- [ ] `latest.json` is maintained as a symlink
- [ ] Watcher2 imports baseline before plan/research via `--import-state`
- [ ] `baseline_*` namespace is enforced and collision-tested
- [ ] Retention policy is enforced (keep latest 5 artifacts)
- [ ] Tests added covering deterministic hash generation, rebuild logic, state import/export, and retention
- [ ] Documentation updated covering manifest format, rebuild rules, summary cache behavior, and cleanup policy
- [ ] Requirement traceability updated (`ARCHITECTURE.md`, `scripts/req_coverage.py`, req-marked tests)

## Alternatives Considered

1. **Always rebuild baseline on every run.**
   - Rejected: removes most benefit and adds avoidable runtime cost.

2. **Date-based daily baseline only.**
   - Rejected: misses same-day source edits and causes stale context risk.

3. **Keep only lossy summaries.**
   - Rejected: can drift from source doctrine; must preserve selected verbatim canonical sections.

4. **Full vector RAG replacement.**
   - Rejected: this FR targets deterministic reuse of known stable corpus, not retrieval recall improvements.

## Related

- GitHub Issue #208 (This implementation)
- FR-276: Prompt caching (Phase 1 only)
- FR-269: CLI state import/export chain

---

## Judgement

**Verdict: APPROVED. Scope frozen. Implementation authority granted.**

### Critical Review (2026-04-25 23:02)

All 8 evaluation criteria PASSED:

1. ✅ **Scope**: Clear and minimal - watcher2-only baseline checkpointing with deterministic hash invalidation
2. ✅ **Consistency**: No contradictions, technical choices explicit (Option B for summary determinism)
3. ✅ **Measurability**: 14 acceptance criteria are testable with clear pass/fail conditions
4. ✅ **Feasibility**: Strong foundation on FR-269 state import/export and proven hash-based patterns
5. ✅ **Architecture**: Follows established 3-layer pattern, explicitly avoids core framework changes
6. ✅ **Single Responsibility**: Focused solely on cross-run baseline caching, no bundled concerns
7. ✅ **Classification**: Integration-level feature with 1-2 specific use cases (watcher2 pipeline)
8. ✅ **Tests**: All 13 acceptance tests compile and fail for correct reason (ModuleNotFoundError)

**Research validated**: Competitive analysis confirms no existing framework provides deterministic baseline checkpointing. Usage evidence shows genuine need in watcher2 pipeline for token cost optimization.

**Acceptance tests validated**: All tests properly fail with `ModuleNotFoundError` for missing implementation modules, confirming RED state compliance with TDD discipline.

---

## Research Brief

### Competitive Landscape

**LangGraph** (foundational dependency): Provides core checkpointing via `MemorySaver`, `SqliteSaver`, and `RedisSaver`, but these are session-scoped for interrupt/resume workflows. No cross-run baseline caching exists at the framework level.

**CrewAI** (49.2K stars): Unified memory system with scope trees (`/project/alpha`, `/agent/researcher`) and composite scoring (semantic + recency + importance). Memory persists knowledge across crew executions but is focused on contextual recall rather than deterministic baseline checkpointing. Uses LLM inference for memory organization, making it non-deterministic.

**Pydantic AI** (16.5K stars): AgentSpec YAML definitions with capability composition, but single-agent scoped with no cross-run state persistence. Built-in "Compaction" capabilities for OpenAI/Anthropic but these are runtime memory management, not baseline checkpointing.

**DSPy** (33.8K stars): Compiler-driven prompt optimization with automatic tuning, but focused on training-time optimization rather than runtime caching patterns.

No competing framework provides deterministic, hash-based baseline checkpointing for stable corpus reuse across pipeline runs. Most solutions focus on session memory or contextual recall rather than content-addressed precomputation.

### Existing Abstractions

**State Export/Import (FR-269)**: CLI flags `--import-state <path>` and `--export-state <path>` for inter-run state chaining. Foundation for baseline integration via import mechanism. Located in `yamlgraph/storage/export.py` and `yamlgraph/cli/graph_commands.py`.

**Node-Level Caching (FR-032)**: Implemented LangGraph `CachePolicy` integration with YAML `cache:` field for per-node result caching. TTL-based with state hash cache keys. Located in node factory modules and graph compilation pipeline.

**Checkpointers**: Memory, SQLite, and Redis persistence for session-based checkpoint/resume. Session-scoped, not cross-run. Located in `yamlgraph/storage/checkpointer.py` and related modules.

**Content Hashing**: Used in GitHub Issues Remote Inbox (FR-243) for deduplication via `sha256(content_hash + manifest_version)`. Located in `.chaplain/lib/watcher/inbox_sync.sh`.

**Watcher2 Pipeline**: Shell-based orchestration with state chaining between plan/research/enforce steps. Located in `.chaplain/watcher2.sh` and sourced libraries in `.chaplain/lib/watcher/`.

### Diary Precedents

**Node-Level Cache Trap (2026-04-19)**: "When integrating framework-specific types, always translate at the compilation boundary. YAML config should express user intent; the compiler converts to framework objects." Risk of leaking LangGraph abstractions into YAML layer.

**Watcher2 Infrastructure Constraints (2026-04-22)**: "*Test infrastructure from its deployment context.* A worktree orchestrator must be tested from the main repo, not from a worktree — the environment constraints are different." Environment isolation critical for baseline testing.

**Baseline Performance Validation (2026-04-24)**: "**Acceptance criteria should be empirically validated**: If a criterion requires specific performance, measure against current baseline before implementation." Need concrete baseline for measuring token cost reduction.

**CI Status Shape Mismatch (2026-04-22)**: Silent failures in status checking due to assumption about data shape. Relevance: Baseline hash validation must handle edge cases in file content normalization.

### Usage Evidence

- **Existing graphs using related abstractions**: 31 chaplain graphs, 320 example graphs, 29 files using state export/import patterns
- **Real-world use cases beyond the proposal**: Watcher2 pipeline is the primary consumer (plan → shell → enforce chaining). No other identified use cases in current codebase
- **State chaining patterns**: Used exclusively in watcher2 orchestration for session continuity across shell boundaries

### Classification Signal

- **Abstraction level**: Integration (specific to watcher2 use case)
- **Recommended approach**: Build (no cheaper documentation alternative exists)
- **Key risk**: Over-engineering baseline scope beyond watcher2's actual stable corpus, leading to cache invalidation thrash