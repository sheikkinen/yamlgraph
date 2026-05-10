# Diary: FR-363 Per-node OTel Scoping Reflection

**Date:** 2026-05-10
**FR:** FR-363 Per-node OTel exporter scoping in copilot_node.py
**Author:** watcher2 (validate-gate remediation)

---

## What Happened

FR-363 adds `YAMLGRAPH_OTEL_DIR` support to `_execute_cli` in `copilot_node.py` so each
copilot node subprocess receives a node-scoped `COPILOT_OTEL_FILE_EXPORTER_PATH`:
`<YAMLGRAPH_OTEL_DIR>/<node_name>.otel.jsonl`.

The implementation is a single callsite change (~7 lines) in `_execute_cli`, guarded by an
`os.environ.get("YAMLGRAPH_OTEL_DIR")` check so behavior is completely unchanged when the
variable is absent. The four acceptance tests (AC-01 through AC-04) all pass green and cover:
set path, unset path, two-node distinctness, and session-ID extraction invariance.

Supporting artifacts committed alongside the implementation:
- `tests/unit/test_fr363_per_node_otel_scoping_red.py` — 4 acceptance tests
- `changelog/unreleased/fr-363-per-node-otel-scoping.md` — changelog fragment
- `CLAUDE.md` — `YAMLGRAPH_OTEL_DIR` added to environment variable table

---

## Trap

**`callsite_already_normalized`** — The FR Judgement noted that `os` was absent from
`copilot_node.py`'s imports and would need to be added. In practice `os` was already present
in the module (it was used for nothing else at that point but the import was there). The
implementer's note saying "add `import os`" created a brief false divergence where the
reviewer expected the import to appear as a new addition in the diff.

The lesson: implementer notes in FR Judgement sections are written before inspecting the
callsite. They describe *likely* work, not *guaranteed* work. The notes are pre-commit hints
only; the code is authoritative.

---

## Root Cause

No defects were introduced. The change touches exactly one callsite, adds `import os` (which
was present but is now meaningfully used), and threads `env=node_env` through the existing
`subprocess.run` call. The AC tests verified boundary behavior: `env` is `None` when unset
and contains the correct scoped path when set.

---

## What Worked

1. **Boundary normalization at subprocess entry**: constructing `node_env` at the moment the
   subprocess is launched (not upstream in `create_copilot_node`) keeps the env override
   isolated to the execution boundary, consistent with the Knowledge Graph's
   `the_one_law: Normalize at the boundary where external data enters`.
2. **Opt-in via env var**: zero config surface in graph YAML; existing node tests pass
   unchanged because no default behavior is altered.
3. **Tight AC scope**: four tests, four assertions — one per AC. No speculative coverage
   beyond what the FR specified.
4. **Prerequisite satisfied**: FR-363 unblocks FR-364 (event classification) by making
   per-node OTel files available as distinct inputs to the mining pipeline.

---

## Proportionality Assessment

| Signal | Verdict |
|--------|---------|
| Diff scope vs FR scope | ✅ Proportional — ~7 production lines, 4 tests, changelog/doc updates only |
| AC tests check behavior | ✅ `subprocess.run` mock verifies exact `env` dict at call boundary |
| No speculative flags | ✅ No new YAML config keys; no automatic directory creation |
| Architecture alignment | ✅ Boundary normalization pattern; no Layer 2→Layer 3 drift |
| `YAMLGRAPH_OTEL_DIR` documented | ✅ Added to `CLAUDE.md` environment variable table |

---

## Seed

> FR-363 enables node-level OTel file scoping, but the caller is responsible for creating
> the `YAMLGRAPH_OTEL_DIR` directory. Should a future FR add a `yamlgraph graph run --otel-dir`
> CLI flag that creates the directory automatically and passes `YAMLGRAPH_OTEL_DIR` into the
> subprocess environment — making per-node OTel collection a first-class CLI option rather
> than a raw env-var convention?

This would close the ergonomics gap between "framework primitive" (FR-363) and "user-facing
feature" without touching the node factory code at all — the CLI presentation layer would set
the env var before invoking the graph, exactly as the three-layer separation intends.
