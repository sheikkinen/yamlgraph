# FR-1051: `artifact_hash` ignores `defaults.prompts_relative`

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** XS
**Requested:** 2026-09-18
**First consumer / first event:** the csap voicebot, at the moment it upgrades
past 0.5.23 — attempted 2026-09-18 and reverted. Every one of its 62 scripted
conversations died on the first turn. Reproducible here without that repository
(see *Reproduction*).
**Research:** in-body — a source read of all eight readers of
`prompts_relative` in this repository, tabulated below, every one verifiable
from this checkout. The consumer incident is reproduced here as a runnable
three-line check (see *Reproduction*) rather than cited across repositories:
the consumer's own record is on an unmerged branch and is deliberately **not**
this FR's evidence.
**Prior art:**
- [FR-1050-loop-limits-bind-or-fail.md](FR-1050-loop-limits-bind-or-fail.md) —
  same shape (a setting declared in one place and honoured in another), but a
  different mechanism and surface: that one is about limits that never bind,
  this is one reader disagreeing with seven. Neither fixes the other.
- FR-842 (lint runs the loader's validator) — made lint agree with the loader.
  This FR makes the artifact hash agree with both. Same direction, next module.

## Summary

`yamlgraph/utils/artifact_hash.py:43` reads `prompts_relative` from the graph's
top level only. Every other reader falls back to `defaults:`. A graph that
declares its prompt settings under `defaults:` — the documented place — fails
the artifact hash at runtime while compiling and linting cleanly.

## Problem

```python
# yamlgraph/utils/artifact_hash.py:40-43
prompts_dir      = config.get("prompts_dir") or (config.get("defaults") or {}).get("prompts_dir")
prompts_relative = config.get("prompts_relative", False)
```

The two settings are read asymmetrically, two lines apart: `prompts_dir` falls
back to `defaults:`, `prompts_relative` does not.

Every reader of `prompts_relative` in the repository:

| reader | reads |
|---|---|
| `compile/graph_loader.py:108` | top-level **or** `defaults` |
| `linter/checks.py:95` | top-level **or** `defaults` |
| `compile/map_compiler.py:304` | `defaults` |
| `compile/node_compiler.py:151` | effective `defaults` |
| `node_factory/llm_nodes.py:100` | `defaults` |
| `node_factory/race_node.py:350` | `defaults` |
| `tools/agent.py:196` | `defaults` |
| **`utils/artifact_hash.py:43`** | **top-level only** |

One of eight disagrees, and it is the newest.

### What the consumer saw

`graphs/flex_navigator/graph.yaml` declares under `defaults:`:

```yaml
defaults:
  prompts_relative: true
  prompts_dir: prompts
```

The hash therefore computes `prompts_dir='prompts'` with
`prompts_relative=False`, which resolves nothing:

| settings | resolves |
|---|---|
| `'prompts'`, `True` — what the graph declares | yes |
| `'prompts'`, `False` — what `artifact_hash` computes | **no** |

```
ValueError: Cannot hash executable artifact: unresolved prompt
'classify_intents' referenced by graphs/flex_navigator/graph.yaml
```

The graph compiles. It lints. It passes 3255 unit tests. It cannot hold one
conversation. The failure needs an executed call to appear, so the consumer
found it only in a full end-to-end suite — 0 of 62 — after everything cheaper
had gone green.

## Ideal Result

A graph's prompt settings mean the same thing to every part of the engine that
reads them, wherever the author declared them. No module is the one that
disagrees.

## Proposed Solution

One line — but **not** the `or` form used two lines above it. `or` falls
through on any falsey value, so an explicit top-level `prompts_relative: false`
would be overridden by a `defaults:` value of `true`, inverting the precedence
AC-03 requires. The presence-based form is correct:

```python
prompts_relative = config.get(
    "prompts_relative", (config.get("defaults") or {}).get("prompts_relative", False)
)
```

Absent at top level → fall back to `defaults`. Present at top level → used,
including an explicit `false`.

Note that `prompts_dir` on line 40 has the same `or` latency for an explicit
empty string. That is not this FR's defect and is not fixed here; AC-03 pins
the correct semantics for the line being changed.

## Reproduction

Runnable in this repository, no consumer checkout needed:

```python
from pathlib import Path
from yamlgraph.utils.artifact_hash import _resolve_graph_prompt
# a graph whose defaults declare prompts_dir: prompts and prompts_relative: true
_resolve_graph_prompt("some_prompt", graph_path, "prompts", True)   # resolves
_resolve_graph_prompt("some_prompt", graph_path, "prompts", False)  # FileNotFoundError
```

The second call is what `compute_artifact_hash` makes for such a graph.

## Acceptance Criteria

- [ ] AC-01 RED first: a graph declaring `prompts_dir` and `prompts_relative`
  under `defaults:` and referencing a prompt fails `compute_artifact_hash` with
  the unresolved-prompt `ValueError`. Fixture committed; RED commit recorded.
- [ ] AC-02 After the fix that graph hashes successfully, and the hash covers
  the resolved prompt file.
- [ ] AC-03 Top-level declaration still works and still wins over `defaults`,
  **including an explicit top-level `false` against a `defaults: true`** — the
  case an `or` fallback would get wrong.
- [ ] AC-04 A graph with neither declaration is unchanged (`False`, no
  fallback surprise).
- [ ] AC-05 A witness pins the agreement itself: every module reading
  `prompts_relative` resolves the same value for one fixture graph declaring it
  under `defaults:`. This is what would have caught the defect.
- [ ] AC-06 Full unit suite green; RED and GREEN as separate commits, both IDs
  recorded; changelog fragment and a diary entry with `Seed:`.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Fix it in the consumer — hoist `prompts_relative` out of `defaults:` | **Rejected.** A one-line workaround in one graph for an engine defect that hits the next graph to declare it the documented way. The consumer explicitly declined it. |
| A2 | Make `artifact_hash` take the already-parsed `GraphConfig` instead of re-reading the YAML | Deferred, and the better long-term shape — the config object already resolves this correctly. Larger change, and the one-line fix is what unblocks the consumer today. Worth its own FR. |
| A3 | Normalise prompt settings at load and forbid the top-level form | Rejected here: a breaking change to graph syntax to fix a one-line asymmetry. |

## Related

- `yamlgraph/utils/artifact_hash.py` — the defect, new since 0.5.17.
- csap NC-525 — the reverted upgrade this blocks.
