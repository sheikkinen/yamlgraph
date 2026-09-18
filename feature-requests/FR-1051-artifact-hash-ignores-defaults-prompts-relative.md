# FR-1051: `artifact_hash` ignores `defaults.prompts_relative`

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced
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

For one graph, `compute_artifact_hash` resolves `prompts_relative` to the same
value the loader's `GraphConfig` does — whether the key is absent, top-level
`true`, top-level `false`, or present only under `defaults:`.

**Deliberately narrower than "every reader agrees."** `linter/checks.py:94-98`
uses a falsey `or` fallback, so an explicit top-level `false` against
`defaults: true` will still disagree with the loader after this FR. That is a
real second defect and it is **parked for its own FR** (judgement R-2) — this
one fixes the seam that breaks execution.

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

- [x] AC-01 RED first, and it **condemns** rather than records the defect: a
  fixture graph with `defaults.prompts_dir`, `defaults.prompts_relative: true`
  and a referenced local prompt **hashes successfully, and its hash changes
  when that prompt file changes**. On the baseline this fails, because
  `compute_artifact_hash` raises the unresolved-prompt `ValueError`; after the
  fix the same test passes unmodified. RED commit ID recorded.
- [x] AC-02 Top-level `prompts_relative` still wins over `defaults:`,
  **including an explicit top-level `false` against `defaults: true`** — the
  case an `or` fallback gets wrong.
- [x] AC-03 A graph declaring neither resolves `False`, unchanged.
- [x] AC-04 For one fixture graph in each of the four states (absent, top-level
  `true`, top-level `false`, `defaults` only), `compute_artifact_hash` uses the
  same `prompts_relative` the loader's `GraphConfig` computes. This is the
  governed seam, and no claim is made about other readers (R-2).
- [x] AC-05 Every new test carries `@pytest.mark.req("REQ-YG-552")`, matching
  the existing artifact-hash witnesses in
  `tests/unit/test_fr807_route_evidence_record.py`, and
  `python scripts/req_coverage.py --strict` passes.
- [x] AC-06 `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` and
  `ruff check yamlgraph/` pass. RED and GREEN are separate commits, both IDs
  recorded, plus the changelog fragment, the FR implementation record, and a
  diary entry with `Seed:`.

## Implementation record

**Status:** Enforced 2026-09-18 on `feat/fr-1051-enforce`.

| Commit | Content |
|---|---|
| `3b9159ed` | RED — two REQ-YG-552 witnesses in `tests/unit/test_fr807_route_evidence_record.py`: the defaults-only fixture raised `ValueError: Cannot hash executable artifact: unresolved prompt 'fr1051_probe'`, and the parameterized loader-parity case `[None-True]` asserted `False is True`. The other three precedence states passed on the baseline, as expected. |
| `61c064ea` | GREEN — `yamlgraph/utils/artifact_hash.py` presence-based fallback; both witnesses pass unmodified. |

**Decisions.**
- The parity witness (AC-04) observes the hasher's effective `prompts_relative`
  through resolution outcome: the fixture's only prompt copy lives in
  `<graph dir>/prompts/`, so hashing succeeds exactly when the setting is
  `true`. The assertion is `hash_succeeded is GraphConfig.prompts_relative` —
  the loader is the oracle, not a hard-coded expectation.
- `ruff format` split the new expression across lines; the `dict.get(key,
  default)` form and its precedence are unchanged (C-2 held, no `or`).

**Deviations.** None. Production scope stayed at
`yamlgraph/utils/artifact_hash.py` (C-4); `prompts_dir` `or` latency and the
linter's falsey fallback (R-2) remain parked and untouched.

**Validation.** `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` →
6853 passed, 61 skipped, 1 xfailed. `ruff check yamlgraph/` and
`python scripts/req_coverage.py --strict` pass.

One validation misstep worth recording: the first full-suite run reported
`test_ramp_installer.py::test_wrapper_delegates` failing with
`ModuleNotFoundError: No module named 'yaml'`. The cause was the invocation,
not the code — `.venv/bin/python -m pytest` leaves the venv off `PATH`, so the
test's `subprocess` call to `scripts/ramp.sh` got the system interpreter. With
the venv activated the file passes 45/45.

## Research record

**Is this a graph?** No. This is deterministic configuration resolution — one
dict lookup with a fallback. There is no per-item model evaluation and no
multi-stage pipeline, so no research or authoring graph in this repository
fits; the solution classes below were enumerated by source read.

| # | Solution class | Disposition |
|---|---|---|
| A1 | **The one-line presence-based fallback** (proposed) | **Adopted.** Smallest change that makes the hash agree with the loader; unblocks the first consumer today. |
| A2 | Fix it in the consumer — hoist `prompts_relative` out of `defaults:` | Rejected. A workaround in one graph for an engine defect that hits the next graph declaring it the documented way. The consumer explicitly declined it. |
| A3 | Pass the parsed `GraphConfig` into `artifact_hash` instead of re-reading the YAML | **Deferred, and the better long-term shape** — the config object already resolves this correctly, and doing so removes the whole class rather than one instance. Larger surface (callers, signature); worth its own FR once this is unblocked. |
| A4 | Extract a shared presence-based resolver and migrate all eight readers to it | Deferred. Strictly better than A3 for the class, and strictly worse as a first move: it changes linter precedence semantics (R-2's parked defect) in the same commit as an execution-blocking fix, so a regression could not be attributed. Sequence it after A1 and A3. |
| A5 | Normalise prompt settings at load time and forbid the top-level form | Rejected. A breaking change to graph syntax to fix a one-line asymmetry. |
| A6 | Make `artifact_hash` tolerate an unresolved prompt (warn, skip the file) | Rejected. It would hash an artifact while silently omitting part of it, which defeats the point of an artifact hash — a worse failure than the loud one. |

## Related

- `yamlgraph/utils/artifact_hash.py` — the defect, new since 0.5.17.
- csap NC-525 — the reverted upgrade this blocks.
