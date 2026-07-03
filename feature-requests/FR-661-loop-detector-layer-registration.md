# Feature Request: Register loop_detector in import-linter layer config

**Priority:** LOW
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-03
**Judged:** 2026-07-03

## Summary

`yamlgraph/loop_detector.py` (extracted from `graph_loader.py` in FR-658) is not listed in any `.importlinter` layer. It passes the contract only because unlisted modules are unconstrained. This is accidental correctness.

## Value Statement

Import-linter enforces architectural boundaries only for modules it knows about — registering `loop_detector` closes a gap where a future import could silently violate the three-layer contract.

## Problem

The `.importlinter` config lists Layer 2 modules explicitly:

```
yamlgraph.graph_loader : yamlgraph.node_factory : yamlgraph.executor : ...
```

`loop_detector` is not in any layer. It is imported by:
- `graph_loader.py` (Layer 2) — `apply_loop_node_defaults`
- `linter/checks_semantic.py` (Layer 2) — `detect_loop_nodes`

If someone added a Layer 2 import inside `loop_detector.py`, the linter would not catch it. The module is a pure utility (zero yamlgraph imports) and should be explicitly placed.

## Proposed Solution

**Option A (approved):** Add to Layer 3 (Side Effects) alongside other pure utilities.

```ini
# .importlinter Layer 3 line:
yamlgraph.tools : yamlgraph.models : yamlgraph.utils : ... : yamlgraph.loop_detector
```

This is correct: `loop_detector` has zero dependencies, is importable by any layer, and lives conceptually alongside `error_handlers` and `verification` (both already Layer 3).

## Acceptance Criteria

- [ ] AC-1: `loop_detector` listed explicitly in `.importlinter` Layer 3
- [ ] AC-2: `lint-imports` exits 0
- [ ] AC-3: Import linter test passes

## Judgement

**Verdict: Approved. Option A (Layer 3).**

Verified: `loop_detector` is absent from all `.importlinter` layer definitions. The module has zero yamlgraph imports — it's a pure graph-theory utility (`detect_loop_nodes` does DFS cycle detection, `apply_loop_node_defaults` patches a dict). Layer 3 is the correct placement: it's importable by all layers (Layer 2 already imports it from `graph_loader.py` and `linter/checks_semantic.py`), and adding it to Layer 2 would pointlessly restrict Layer 3 access.

**No amendments needed.** The FR is minimal, clear, and the three ACs are sufficient. Option B (Layer 2) and the alternative of moving to `utils/` are correctly dismissed — Layer 2 is over-restrictive, and the file move disrupts 16+ test imports for no architectural gain.

**Implementation note:** This is a one-line change to `.importlinter`. The 0.5 day estimate is generous — 10 minutes including test verification. Consider bundling with FR-660 if they're enforced in the same session.

**Scope freeze:** Add `yamlgraph.loop_detector` to the Layer 3 line in `.importlinter`. Nothing else.

## Alternatives Considered

- **Move to `yamlgraph/utils/loop_detector.py`**: Automatically Layer 3 via the `yamlgraph.utils` prefix. More disruptive (changes import paths in 3 files + 16 test imports).
- **Leave as-is**: Works today but relies on import-linter's unconstrained-module behaviour.
- **Add to Layer 2**: Over-restrictive — prevents Layer 3 modules from importing it.

## Related

- FR-658: Graph-as-tool (extracted `loop_detector.py` from `graph_loader.py`)
- `.importlinter`: Layer config
- FR-218: Import-linter architectural boundaries (CAP-134)
