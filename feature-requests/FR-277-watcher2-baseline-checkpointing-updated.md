# Feature Request: FR-277 Watcher2 Baseline Checkpointing

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 4 days
**Requested:** 2026-04-25

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