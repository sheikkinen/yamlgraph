# Audit Report — Code Quality & Architecture

**Date**: 2026-05-29 | **Version**: 0.5.4

## Linting (ruff)

```
Command: ruff check yamlgraph/
Result:  All checks passed!
```

Zero violations. Ruff covers: pyflakes, pycodestyle, isort, flake8-bugbear, and more.

## Import Boundaries (import-linter)

```
Command: lint-imports
Result:  Contracts: 1 kept, 0 broken.
         Analyzed 115 files, 251 dependencies.
```

Three-layer architecture enforced:
- **Layer 1** (Presentation): `yamlgraph/cli/` — no upstream imports
- **Layer 2** (Logic): `yamlgraph/graph_loader.py`, `yamlgraph/executor.py` — no Layer 1 imports
- **Layer 3** (Side Effects): `yamlgraph/tools/`, `yamlgraph/models/`, `yamlgraph/utils/` — no Layer 1/2 imports

## Module Size

Largest files (max allowed: 450 lines):

| File | Lines | Status |
|------|-------|--------|
| yamlgraph/tools/agent.py | 447 | WARN (at boundary) |
| yamlgraph/node_compiler.py | 447 | WARN (at boundary) |
| yamlgraph/models/state_builder.py | 442 | OK |
| yamlgraph/models/graph_schema.py | 441 | OK |
| yamlgraph/linter/checks_semantic.py | 435 | OK |
| yamlgraph/executor_async.py | 435 | OK |
| yamlgraph/node_factory/llm_nodes.py | 433 | OK |
| yamlgraph/node_factory/copilot_node.py | 400 | OK |
| yamlgraph/graph_loader.py | 400 | OK |

No files exceed the 450-line hard limit. Two files at 447 are near the boundary.

## Cyclomatic Complexity (radon)

```
Command: radon cc yamlgraph/ -a -nc
Result:  47 blocks at grade C (average complexity: 14.06)
         0 blocks at grade D or higher
```

Pre-commit hook `radon CC gate (block grade D)` prevents merging any function at complexity grade D+.

## Code Duplication (jscpd)

```
Command: jscpd yamlgraph/ --min-lines 10
Result:  10 clones found, 0.73% duplicated lines
```

| Metric | Value |
|--------|-------|
| Files analyzed | 113 |
| Total lines | 21,529 |
| Clones found | 10 |
| Duplicated lines | 158 (0.73%) |
| Duplicated tokens | 1,056 (0.81%) |

Top duplication areas:
- `storage/simple_redis.py` — async/sync pattern repetition (3 clones)
- `storage/checkpointer_factory.py` — factory pattern (1 clone)
- `executor.py` / `executor_async.py` — sync/async wrappers (2 clones)

All within acceptable tolerance (< 3%).

## Dead Code (vulture)

```
Command: vulture yamlgraph/ vulture_whitelist.py --min-confidence 80
Result:  No dead code found
```

## noqa Confessions

```
Command: python scripts/noqa_coverage.py
Result:  95 noqa in codebase, 152 confessions documented, 0 undocumented
```

Every suppression is tracked with a CONF-XXX ID, explanation, and justification in `docs/confessions.md`.

## Verdict

**PASS** — Code quality is well-controlled. Architecture boundaries enforced. Complexity gated. No dead code. Minimal duplication.
