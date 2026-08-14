# Feature Request: FR-794 — Shared Python Tool Manifest Root Confinement Fix

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced 2026-08-14 — AC-01..AC-06 delivered; 4/4 new tests green + 18/18 FR-445/FR-768 regression tests green (REQ-YG-588, CAP-227)
**Effort:** 0.5 day
**Requested:** 2026-08-14
**First consumer / first event:** FR-788 (platform-confirm) authoring
run, the first time a `type: python` tool manifest is shared across
step-graph directories in the API discovery pipeline; discovered while
enforcing FR-788, and reproduced against the already-merged FR-785
(`endpoint-probe`) graph as well.

## Summary

`yamlgraph/tools/python_tool.py`'s graph-root confinement check
(FR-445) validates a resolved `type: python` tool `path` against the
*consuming graph's* root directory. `yamlgraph/tools/manifest.py`'s
`_translate()` (FR-768 manifest sharing) correctly resolves a shared
tool's `path:` relative to the *manifest's own* directory instead —
producing a legitimate absolute path that then always fails FR-445's
check whenever the manifest lives in a different directory than the
consumer. The two features are currently incompatible for any shared
`type: python` tool manifest.

## Value Statement

Any graph author reusing a shared Python-runtime tool manifest from a
sibling/parent directory (the exact "one tool, many consumers" pattern
FR-768 was built for) gets a hard runtime crash instead of a working
tool call — silently breaking a documented, already-shipped pattern.

## Problem

Reproduced live against the merged, "Enforced" FR-785 `endpoint-probe`
graph, which consumes `examples/api-discovery/tools/curl_probe.tool.yaml`
(a `type: python` manifest) via `manifest: ../../tools/curl_probe.tool.yaml`:

```
$ yamlgraph graph run examples/api-discovery/steps/endpoint-probe/graph.yaml \
    --var 'candidate_urls=["https://example.com"]' --full
❌ Error: Python tool load failed in strict mode (config.tool_load_mode=strict):
curl_probe: Python tool 'curl_probe': path
'.../examples/api-discovery/tools/curl_probe.py' escapes graph root
'.../examples/api-discovery/steps/endpoint-probe'
(resolved: .../examples/api-discovery/tools/curl_probe.py)
```

The same error blocks FR-788 (`platform-confirm`), which reuses the same
manifest, and will block FR-790 (`schema-extract`, uses the `parse_openapi`
Python manifest) and the FR-791 orchestrator wherever it composes these
step graphs.

**Note:** a second, independent defect (a `schema:`/`output_schema:`
dialect mismatch in `probe.yaml`) was discovered while validating this
fix and is tracked separately in FR-795 (graph-authoring scope, per the
judge's SPLIT verdict on 2026-08-14 — see judgement history below).

**Root cause, precisely:**

- `yamlgraph/tools/manifest.py::_translate()` resolves a `PythonRuntime.path`
  as `(manifest_dir / rt.path).resolve()` — correct, and produces an
  absolute path anchored at the manifest's own directory. It performs
  **no confinement check of its own** against `manifest_dir` (a
  separate, currently-unguarded gap — a manifest's `path:` could
  currently point anywhere on disk with zero validation).
- `yamlgraph/tools/python_tool.py::_resolve_python_tool_path()` then
  re-validates that already-resolved absolute path against
  `graph_root` (the *consuming* graph's directory) — the wrong
  boundary for a manifest-declared tool, which was never meant to live
  inside the consumer's directory tree.

## Ideal Result

A graph in directory A can declare
`tools: { curl_probe: { manifest: ../../tools/curl_probe.tool.yaml } }`
and successfully load and call the tool, while a manifest whose own
`path:` escapes *its own* directory is still rejected at compile time,
and an inline (non-manifest) graph tool whose `path:` escapes the
*consuming graph's* directory is still rejected exactly as FR-445
requires today (zero regression on FR-445's existing acceptance tests).

## Proposed Solution

1. In `yamlgraph/tools/manifest.py::_translate()`: when translating a
   `PythonRuntime` with `path`, validate
   `resolved.relative_to(manifest_dir)` and raise `ValueError` on escape
   (mirrors the existing `schema_loader` confinement pattern cited in
   FR-445). This closes the currently-unguarded manifest-path gap.
   Stash the trusted boundary as `translated["declared_root"] = str(manifest_dir)`.
2. In `yamlgraph/tools/python_tool.py`:
   - Add `declared_root: str | None = None` to `PythonToolConfig`.
   - In `parse_python_tools()`, populate
     `declared_root=config.get("declared_root")`.
   - In `load_python_function()` / `_resolve_python_tool_path()`: when
     `config.declared_root` is set, confine against that root instead
     of `graph_root` (the path was already resolved absolute by
     `_translate` from exactly that root, so this re-validates the
     *correct* boundary rather than skipping validation).
   - When `declared_root` is unset (inline, non-manifest tools), keep
     today's `graph_root`-confinement behavior byte-for-byte — zero
     change for FR-445's existing AC-01..AC-05.
3. No change to shell-runtime or graph-runtime manifest translation
   (unaffected by this bug).

## Alternatives Considered

| Alternative | Why not |
|---|---|
| Relax `python_tool.py` to skip confinement entirely for manifest-sourced paths | Removes the security boundary FR-445 exists for instead of relocating it correctly; a manifest `path:` could then point anywhere with no check. |
| Duplicate `curl_probe.py`/`parse_openapi.py` per consuming step directory | Defeats the "one tool, many consumers" design goal FR-768/FR-783/FR-788 all state explicitly; multiplies maintenance surface. |
| Set `tool_load_mode: warn` on affected graphs | Confirmed not a fix — it only silences the crash; the tool is still absent from `callable_registry`, so the agent cannot call it. |

## Acceptance Criteria

- [ ] AC-01: RED test reproduces the exact failure via
  `yamlgraph.compile.graph_loader.load_and_compile` on a temp fixture:
  a `type: python` manifest in directory A consumed via
  `manifest: ../b/tool.tool.yaml`-style reference from graph directory B
  currently raises the "escapes graph root" `ValueError`.
- [ ] AC-02: After the fix, that same fixture loads and compiles
  successfully AND invoking the compiled `StateGraph` (e.g. `.invoke({})`
  on the FR-445 harness's minimal `def run(state): return {'ok': True}`
  fixture tool, now reached through a manifest reference instead of an
  inline declaration) returns the tool's actual output — proving the
  manifest-backed Python callable executed, not merely that compilation
  didn't raise. No new public callable-registry API is introduced.
- [ ] AC-03: A manifest whose own `path:` escapes its *own* manifest
  directory is rejected at compile time with an explicit error (new
  protection, since this path was previously unchecked).
- [ ] AC-04: All existing FR-445 tests
  (`tests/unit/test_fr445_python_tool_graph_root_confinement_red.py`)
  still pass unmodified — inline (non-manifest) `type: python` tools
  keep graph-root confinement exactly as before.
- [ ] AC-05: `examples/api-discovery/steps/endpoint-probe/graph.yaml`
  (FR-785, merged) tool-loading no longer raises the "escapes graph
  root" error for `curl_probe` (verified at the `_parse_all_tools`
  seam); full end-to-end `load_and_compile` success is blocked on the
  separate FR-795 prompt-schema repair and is NOT required by this FR.
- [ ] AC-06: Changelog fragment and diary reflection.

## Related

- FR-445 (python-tool-path-root-confinement — the check being relocated, not removed)
- FR-768 (tool manifest declaration/reuse — the sharing pattern this repairs)
- FR-783 (curl_probe manifest — the first real-world tool hitting this)
- FR-785 (endpoint-probe — merged, currently broken at runtime by this bug)
- FR-788 (platform-confirm — blocked by this bug; resumes once this lands)

**Prior art:** No existing FR addresses the manifest/root-confinement
interaction; FR-445 and FR-768 were each judged/enforced independently
and their combination was never exercised end-to-end with a real
cross-directory `type: python` manifest until FR-788's authoring run.

**Judgement revisions folded:** R-1 (AC-02 rewritten to an observable
invocation-based assertion — no reliance on a nonexistent public
callable-registry surface) — see
`feature-requests/FR-794-python-tool-manifest-root-confinement-fix.judgement.md`.

**Scope expansion attempted and reverted (2026-08-14):** briefly expanded
to also fix `probe.yaml`'s schema dialect (human-directed), but the judge
rendered a SPLIT verdict — framework confinement fix and graph-artifact
prompt repair have different execution routes and must not share one
implementation authority. Reverted to framework-only scope; the prompt
fix is tracked as FR-795.

## Implementation Notes

- Fixed `yamlgraph/tools/manifest.py::_translate()`: manifest-declared
  `PythonRuntime.path` is now validated against its own `manifest_dir`
  (new `ValueError` on escape — closes the previously-unguarded gap)
  and the resolved directory is carried forward as `declared_root`.
- Fixed `yamlgraph/tools/python_tool.py`: added `declared_root` to
  `PythonToolConfig`; `load_python_function` confines against
  `declared_root` when present (manifest-sourced tools), falling back
  to `graph_root` unchanged for inline tools — zero behavior change for
  FR-445's original AC-01..AC-05.
- New tests: `tests/unit/test_fr794_python_tool_manifest_root_fix.py`
  (4 tests: cross-directory manifest tool loads and executes via a
  compiled graph invocation, manifest-self-escape rejected, inline-tool
  regression, and FR-785's `curl_probe` tool-loading seam no longer
  raises the escape error). All 18 existing FR-445 + FR-768 tests still
  pass unmodified.
- AC-05 is intentionally narrow per the judge's C-7: it proves the
  tool-loading seam only, not full graph compile — FR-785's
  `endpoint-probe` graph still fails `load_and_compile` on the separate,
  independent `probe.yaml` schema-dialect bug, now tracked as FR-795.
- `capabilities/CAP-227` (REQ-YG-588) added; `ARCHITECTURE.md`
  regenerated; `req_coverage.py --strict` clean.
