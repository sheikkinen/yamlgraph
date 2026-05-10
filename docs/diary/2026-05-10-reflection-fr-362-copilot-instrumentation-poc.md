# Diary: FR-362 Copilot Instrumentation Process-Mining POC

**Date:** 2026-05-10
**FR:** FR-362 Copilot instrumentation process-mining POC
**Author:** watcher2 (post-validate sanity reviewer)

---

## What Happened

FR-362 added three local tooling artifacts for instrumenting a two-phase Copilot run (`plan` → resumed `implement`) and extracting normalized process events:

1. `scripts/copilot_instrument.sh` — disposable-worktree runner with per-phase artifact capture (prompt, stdout JSONL, stderr, `--share` markdown, OTel JSONL, debug log, git status/diff snapshots).
2. `scripts/extract_copilot_events.py` — Pydantic-validated JSONL event extractor from OTel span and git diff artifacts.
3. `docs/copilot-instrumentation-poc.md` — findings document enumerating candidate YAMLGraph node types.

All 90 lines of RED acceptance tests in `tests/unit/test_fr362_copilot_instrumentation_poc_red.py` pass. No changes were made to `yamlgraph/` production runtime code, matching the FR's "no framework integration" constraint.

---

## Trap

**`data_boundary_as_scope_creep`** — The temptation when writing the extractor was to also parse the CLI `stdout.jsonl` artifact and the `--share` markdown for events, since those are structurally richer than OTel span data for early runs. The constraint says "normalize at the boundary where external data enters" and the boundary here is OTel + git diff — not the full artifact set. Starting with the minimal event types (two sources) prevents speculative over-engineering and preserves the single responsibility of the first pass.

---

## Root Cause

No root cause defect to report — this was a greenfield POC with correctly scoped constraints. The main discipline challenge was resisting the "while I'm here" impulse to expand event extraction to all artifact types before the minimal contract was tested and merged.

---

## What Worked

1. **Disposable worktree boundary**: `copilot_instrument.sh` creates and tears down a fresh worktree for each run, keeping instrumentation artifacts out of the main worktree and matching the `.gitignore` data boundary for `outputs/`.
2. **Pydantic at the extraction boundary**: `CopilotEvent` model validates every emitted JSONL event, catching malformed OTel or git diff inputs at the extraction step rather than downstream in analysis.
3. **Typed phase enum**: `RunPhase(str, Enum)` ensures only `plan` and `implement` are valid phase identifiers across the extractor and tests, eliminating string drift.
4. **Minimal RED tests first**: Acceptance tests verified file existence, Pydantic model fields, and script structure before implementation details were settled — the tests drove the contract, not the other way around.

---

## Proportionality Assessment

| Signal | Verdict |
|--------|---------|
| Diff scope vs FR scope | ✅ Proportional — 3 deliverables, zero runtime changes |
| Test assertions check behavior | ✅ Structural and behavioral (file existence, schema fields, Pydantic validation) |
| No speculative flags or extensibility | ✅ Two event types only; no conformance scorer in scope |
| Data boundary respected | ✅ Raw artifacts gitignored; only scripts and extractor committed |

---

## Seed

> When OTel span artifacts are absent (a run completes with no spans emitted), the extractor emits zero events for the `otel_span` type. Is there a minimal heuristic — count of spans vs. count of git diff hunks — that could flag "this run produced no observable telemetry" and prompt re-instrumentation before the analysis step?

A future FR could add a run-completeness check: if both `otel.jsonl` and `git-diff.patch` are empty for a phase, emit a synthetic `no_telemetry` event with severity `warn` rather than silently producing an empty JSONL. This would surface instrumentation gaps in the event stream itself.
