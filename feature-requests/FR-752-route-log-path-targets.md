# FR-752: Extend YAMLGRAPH_ROUTE_LOG Path Targets for Route Overlay Workflows

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Completed (enforced 2026-07-19)
**Effort:** 1 day
**Requested:** 2026-07-19
**First consumer / first event:** graph authors running repeated `graph run -> graph export --overlay` loops; first event = they set `YAMLGRAPH_ROUTE_LOG` in `.env` to a reusable path target and run from a fresh workspace.

## Summary

Extend `YAMLGRAPH_ROUTE_LOG` path behavior so it accepts practical path targets for route capture workflows, not just a pre-existing file path. Keep the existing semantics (`1` = logger only, file path = append JSONL) and add boundary-normalized path handling that removes setup friction.

## Value Statement

Route-overlay users get one stable `.env` setting that always produces a usable route log file, reducing setup/debug friction from "why no overlay file" to a deterministic path contract.

## Problem

FR-723 introduced `YAMLGRAPH_ROUTE_LOG` with file-path support. In practice, teams use `.env` for persistent settings and expect path-like values to "just work" across runs and machines. Current behavior is strict enough that valid intent can fail at runtime setup boundaries (non-existent parent directories, directory values, relative path ambiguity).

That creates avoidable friction in the exact loop this feature serves:

1. Set `YAMLGRAPH_ROUTE_LOG` in `.env`
2. Run graph
3. Export overlay from the route JSONL

When path handling is brittle, step 2 succeeds but step 3 fails due to missing or mislocated route files.

## Ideal Result

A user can set `YAMLGRAPH_ROUTE_LOG` once in `.env` using either a file path or a directory target and always get a route JSONL file in a predictable location. The runtime normalizes at the boundary, creates required directories, and emits clear diagnostics only when the target is truly invalid.

## Proposed Solution

Implement a strict, explicit path contract for `YAMLGRAPH_ROUTE_LOG`:

1. Preserve existing modes:
   - `YAMLGRAPH_ROUTE_LOG=1` -> logger namespace only (`yamlgraph.route`), no file output.
   - `YAMLGRAPH_ROUTE_LOG=<file-path>` -> append raw JSONL to file.

2. Extend path mode to support directory targets:
   - If the value resolves to an existing directory, write to `<dir>/route.jsonl`.
   - If the value ends with a trailing separator, treat as directory intent and create it, then write `<dir>/route.jsonl`.

3. Parent creation and normalization:
   - For file-path mode, create parent directories automatically (`mkdir -p` semantics).
   - Resolve relative paths against current working directory (same boundary used by graph CLI).

4. Safety and diagnostics:
   - Never raise from route emission path (keep FR-723 resilience guarantee).
   - Emit one warning on invalid targets (e.g., path points to a special file) and continue logger-only.

5. Documentation updates:
   - Clarify path contract in CLI and graph-yaml reference pages with examples for file and directory modes.

```bash
# logger only
YAMLGRAPH_ROUTE_LOG=1

# explicit file
YAMLGRAPH_ROUTE_LOG=outputs/routes/reflexion.route.jsonl

# directory target (new)
YAMLGRAPH_ROUTE_LOG=outputs/routes/
# writes outputs/routes/route.jsonl
```

## Acceptance Criteria

- [x] AC-01 Existing behavior unchanged: `1` remains logger-only; explicit file path still appends JSONL.
- [x] AC-02 Directory target support: existing directory values write to `<dir>/route.jsonl`.
- [x] AC-03 Parent auto-create: non-existing parent directories are created for file-path mode.
- [x] AC-04 Relative path determinism: file location is stable and documented as CWD-relative.
- [x] AC-05 Invalid target resilience: runtime does not raise; warning emitted; run continues.
- [x] AC-06 Tests added for all modes and edge cases.
- [x] AC-07 Documentation updated (`reference/graph-yaml.md`, `reference/cli.md`).

## Alternatives Considered

1. Do nothing (keep strict file-only expectation).
   - Rejected: preserves avoidable setup friction in overlay workflows.

2. Add a new env var (`YAMLGRAPH_ROUTE_FILE`) for file sink.
   - Rejected: duplicates config surface; `YAMLGRAPH_ROUTE_LOG` already owns route sink intent.

3. Add a CLI flag to `graph run` for route log output path.
   - Deferred: potentially useful, but this FR scopes to env boundary normalization only.

## Related

- FR-723: execution path visualization (route hook + mermaid export + overlay)
- `yamlgraph/utils/route_log.py`
- `reference/graph-yaml.md` (Observability)
- `reference/cli.md` (graph export / overlay usage)

## Judgement (2026-07-19)

**Verdict: AUTHORITY GRANTED** -- scope frozen with the pins below.

Claims verified against source before judging: `yamlgraph/utils/route_log.py`
currently treats any non-boolean env value as a file path and calls
`logging.FileHandler(value)` directly; missing parents, directory targets,
and trailing-separator intent all fail in `_ensure_file_sink()` and are
silently suppressed by `emit_route()` (no warning emitted). Docs currently
describe only logger mode (`1`) and explicit file mode.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | The proposed value statement depends on behavior that does not exist today: path-like values fail silently when parent dirs do not exist or the target is a directory. | Implement boundary normalization in `_ensure_file_sink()` before opening handlers: resolve env path, classify target intent (file vs directory), create required directories, and only then open the sink. |
| F2 | Directory intent is underspecified and risks non-determinism if inferred heuristically. | Directory mode is frozen to two explicit predicates only: (a) resolved target exists and `is_dir()`; or (b) raw env value ends with `os.sep` (and on Windows, also `os.altsep` when present). In both cases sink path is `<dir>/route.jsonl`. |
| F3 | Invalid target resilience is required, but "silent fallback" would violate observability doctrine and make failures hard to diagnose. | Preserve FR-723's never-raise guarantee, but add one warning per target value when sink setup fails (logger name stays `yamlgraph.route`; run continues with logger-only emission). Repeated route events must not spam warnings. |
| F4 | AC-04 and AC-07 are too soft unless path determinism and examples are pinned together. | Relative paths are CWD-relative (process working directory at run time); this wording must appear in both `reference/graph-yaml.md` and `reference/cli.md` with examples for: `1`, explicit file, existing dir, and trailing-separator dir intent. |
| F5 | AC-06 says "all modes and edge cases" but does not enumerate the condemning set; enforce could under-test and still claim pass. | Test matrix is frozen: existing `1` mode unchanged; explicit file append unchanged; file parent auto-create; existing dir -> `route.jsonl`; trailing-separator dir intent with create; invalid target (e.g., special file path) warns once + continues; no raises on emit path. |

**Purge list:** No new CLI flags, no schema changes, no route payload shape changes.

**Scope frozen:** Extend env path-target semantics only.

### Questions for the human (as options, or 'none')

None -- judgement pins A for both decisions: default filename is
`route.jsonl`, and invalid targets warn once then continue in logger-only
mode.

## Enforcement Notes (2026-07-19)

- Implemented boundary normalization in `yamlgraph/utils/route_log.py`:
   - Existing directory target -> `<dir>/route.jsonl`.
   - Trailing separator intent (`os.sep` / `os.altsep`) -> create directory and write `<dir>/route.jsonl`.
   - File-target parent auto-create (`mkdir -p` semantics).
   - Relative path resolution is CWD-relative.
   - Invalid targets warn once per env value and route emission continues logger-only.
- Added/updated tests in `tests/unit/test_route_log.py` for the frozen matrix.
- Updated docs in `reference/graph-yaml.md` and `reference/cli.md` with path-target contract and examples.
