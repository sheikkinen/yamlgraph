# Feature Request: Demo Coverage Gate

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — APPROVED (scope reduced)
**Effort:** 0.5 days (Phase 1: node_type_coverage.py) + 0.5 days (Phase 2: demo_coverage.sh)
**Requested:** 2026-07-01
**Judged:** 2026-07-01

## Summary

Add `scripts/demo_coverage.sh` that runs a curated set of demos under `coverage.py` to prove framework code is reachable. Any `yamlgraph/` module at 0% after the run is provably dead or integration-only.

## Value Statement

Framework authors detect dead core code (like `stream: true` surviving months unnoticed) mechanically, before it accumulates into false documentation and confused users.

## Problem

Unit tests mock the LLM and exercise code paths in isolation. But mocked tests cannot prove that the real execution path — YAML → graph_loader → node_factory → executor → LLM — actually works end-to-end for each feature.

`create_streaming_node()` had passing unit tests for months while being architecturally unreachable from any real execution path. No demo exercised it, so the dead code was invisible.

The demo garden IS the integration test suite for the framework. But today:
- `test_demos.py` only checks YAML loads (never invokes graphs)
- `demo-gate` checks `demo-output.log` exists (shape, not substance)
- `vulture` finds statically dead code but cannot detect dynamically dead paths (code that compiles fine but no graph configuration ever reaches)

## Proposed Solution

### 1. Coverage script (`scripts/demo_coverage.sh`)

```bash
#!/bin/bash
# Run curated demos under coverage to prove framework paths are reachable.
set -e

DEMOS=(
  "examples/demos/hello/graph.yaml --var name=World --var style=pirate"
  "examples/demos/router/graph.yaml --var text='I am furious'"
  "examples/demos/map/graph.yaml --var topic=coverage"
  "examples/demos/guards/graph.yaml --var input='test input'"
  "examples/demos/data-files/graph.yaml"
  "examples/demos/verification-gate/graph.yaml --var claim='the sky is blue'"
  "examples/demos/git-report/graph.yaml --var repo=."
  "examples/demos/reflexion/graph.yaml --var topic=testing"
  "examples/demos/fan-out/graph.yaml --var topic=coverage"
  "examples/demos/race/graph.yaml --var question='what is 2+2'"
  "examples/demos/subgraph/graph.yaml --var topic=graphs"
  "examples/demos/python-variables/graph.yaml --var name=test"
)

rm -f .coverage.demo
for demo in "${DEMOS[@]}"; do
  printf "▶ %s\n" "$demo"
  coverage run --data-file=.coverage.demo --append --source=yamlgraph \
    -m yamlgraph.cli graph run $demo --full 2>/dev/null || true
done

# CLI commands exercise linter/discovery paths
coverage run --data-file=.coverage.demo --append --source=yamlgraph \
  -m yamlgraph.cli graph lint examples/demos/hello/graph.yaml 2>/dev/null || true
coverage run --data-file=.coverage.demo --append --source=yamlgraph \
  -m yamlgraph.cli graph list 2>/dev/null || true

echo ""
coverage report --data-file=.coverage.demo --skip-covered --show-missing
```

### 2. Enforcement in script (replaces pyproject.toml)

The script itself checks coverage output for 0% lines in critical modules:

```bash
# At end of demo_coverage.sh:
CRITICAL="graph_loader|executor|edge_compiler|llm_nodes|tool_nodes|race_node|subgraph_nodes|conditions|guard_evaluator|data_loader|verification"
ZEROS=$(coverage report --data-file=.coverage.demo 2>/dev/null | grep -E "$CRITICAL" | grep " 0%" || true)
if [[ -n "$ZEROS" ]]; then
  echo "❌ Critical modules at 0% coverage from demos:"
  echo "$ZEROS"
  exit 1
fi
```

### 3. Node type coverage check (Phase 1 — CI gate, no LLM)

A lightweight script that cross-references `NodeType` enum against demo graph files:

```python
# scripts/node_type_coverage.py
"""Verify every NodeType has at least one demo that uses it."""
from yamlgraph.constants import NodeType
# ... scan examples/demos/*/graph.yaml for type: X usage
# Fail if any NodeType member has zero demos
# Allowlist for integration-only types: copilot, interactive_tool
```

This runs in CI as a required check (zero cost, <1s).

## Acceptance Criteria

### Phase 1 (CI gate — ship first)

- [ ] `scripts/node_type_coverage.py` cross-checks `NodeType` enum against `examples/demos/*/graph.yaml`
- [ ] Exits non-zero if any NodeType has zero demo coverage
- [ ] Explicit allowlist for integration-only types (`copilot`, `interactive_tool`)
- [ ] Added to pre-commit config or CI workflow as required check

### Phase 2 (advisory — local/nightly)

- [ ] `scripts/demo_coverage.sh` runs 12 curated demos + 2 CLI commands under `coverage run --append`
- [ ] Handles demo failures gracefully (`|| true`), reports partial coverage
- [ ] Critical modules at 0% cause exit 1
- [ ] Documented in `CLAUDE.md` as local/nightly tool (NOT a CI merge gate)
- [ ] NOT added to CI (API cost + LLM non-determinism = flake risk)

## Design: Curated Set Rationale

Each demo chosen for a unique code path:

| Demo | Unique path exercised |
|------|----------------------|
| hello | Baseline: graph_loader, LLM node, executor |
| router | Router node, edge_compiler conditionals, utils/conditions |
| map | Map node, state_builder parallel branch |
| guards | utils/guard_evaluator, deterministic pre/post guards |
| data-files | data_loader.py |
| verification-gate | verification.py |
| git-report | Agent node, tool_nodes, shell tool |
| reflexion | Loop limits, skip_if_exists, conditional back-edges |
| fan-out | Fan-out edges, edge_compiler parallel paths |
| race | node_factory/race_node, timeout handling |
| subgraph | node_factory/subgraph_nodes, graph composition |
| python-variables | Python nodes, utils/expressions variable resolution |

**Expected result:** ~70-75% framework coverage from demos alone. Combined with unit tests: 90%+.

## Alternatives Considered

1. **Run ALL 75 demos** — Too expensive (API costs, time). Diminishing returns after ~12. Most demos exercise the same `llm` + `python` + `shell` paths.

2. **Mock LLM in demo runs** — Defeats the purpose. The point is proving the real end-to-end path works, not that mocks work (unit tests already do that).

3. **Only unit test coverage** — Status quo. Missed `stream: true` being dead for months. Unit tests prove isolated functions work; demos prove the composition works.

## Related

- FR-633 (CLI --stream flag — would add streaming to coverage set once implemented)
- FR-635 (remove dead stream:true — this FR's script would have caught it earlier)
- `scripts/req_coverage.py` — existing requirement traceability (analogous pattern)
- `examples/demos/tests/test_demos.py` — current structure-only test (loads but never invokes)
- Diary: `docs/diary/diary-2026-07-01-the-unwitnessed-garden.md`
