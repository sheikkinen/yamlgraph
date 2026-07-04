# Feature Request: FR-683 — Referential Integrity as Graph-Tool

**Priority:** HIGH
**Type:** Refactor
**Status:** Judged ✅
**Effort:** 1 day
**Requested:** 2026-07-04
**Judged:** 2026-07-04
**Depends:** FR-658 (graph-as-tool, enforced), FR-664 (ref integrity gate, enforced)

## Summary

Extract the referential integrity check from `persist_genesis.py` into a
standalone validation graph (`ref_check.yaml`) and expose it as a `type: graph`
tool. Agent nodes in both genesis and worldgen can call it to self-correct
during generation — prevention at the source, not post-hoc validation.

## Starting Point

FR-664 delivered `validate_referential_integrity()` as a Python function in
`persist_genesis.py`. FR-667 added `validate_genesis.py` which loads the
function via importlib (hack to avoid relative import failure under
yamlgraph's `spec_from_file_location` tool loader). The function checks
`to`, `participants`, `references`, `members`, `affected_locations` against
a set of defined IDs.

Current call sites:
- `validate_genesis.py` — importlib load, warn-only before persist
- `persist_genesis.py` — direct call, warn-only before writing

Current result: genesis produces zero orphan IDs (verified 2026-07-04),
but the importlib hack is fragile and the validation isn't available to
worldgen's agent nodes during generation.

FR-658 (`type: graph` tool) is enforced and provides the composition
mechanism.

## Problem

1. **importlib hack**: `validate_genesis.py` loads `persist_genesis.py` via
   `importlib.util.spec_from_file_location` because yamlgraph's Python tool
   loader doesn't support relative imports. Fragile — breaks if file moves.

2. **Post-hoc only**: Validation runs after `stubs` LLM call in genesis and
   after `deepen` in worldgen. If orphans are found, the LLM call is wasted.
   The agent can't self-correct.

3. **Not available during deepening**: worldgen's `deepen_events` agent has
   `lookup_canon_page`, `list_canon_ids`, `validate_draft` tools. It can
   check if an entity exists but can't validate referential integrity of its
   own output before returning it. If it drafts a page referencing `aldric`
   without creating `aldric`, the orphan propagates.

## Acceptance Criteria

1. **AC-1**: New graph `examples/novel_fandom/ref_check.yaml` — a minimal
   pipeline: takes `pages` (JSON string or list of entity dicts — graph-tool
   args arrive as `str`, normalize at entry), runs
   `validate_referential_integrity`, returns `{valid, orphan_ids, violations}`.

2. **AC-2**: `ref_check` registered as `type: graph` tool in `worldgen.yaml`
   tools section:
   ```yaml
   ref_check:
     type: graph
     path: ref_check.yaml
     description: "Validate referential integrity of entity pages. Returns orphan IDs."
     input_mapping:
       pages: pages
     output_key: gate_result
   ```
   Output shape frozen: `{"valid": bool, "orphan_ids": [...], "violations": [...]}`
   rendered via `str()`. No prose.

3. **AC-3**: `deepen_events` agent node gets `ref_check` in its tools list.
   Agent can call it on its drafted entities to self-validate before returning.

4. **AC-4**: `validate_genesis.py` **deleted** — the importlib hack dies here.
   Genesis `validate` node keeps `type: python`, tool config repointed to
   `path: nodes/ref_integrity.py, function: ref_check`. The page-flattening
   logic from `validate_genesis.py` moves into `ref_check(state)`. No
   graph-tool indirection inside genesis — that composition belongs to FR-685.

5. **AC-5**: `validate_referential_integrity()` extracted from
   `persist_genesis.py` into `nodes/ref_integrity.py` — **self-contained**
   module: pure function `validate_referential_integrity(pages)` +
   state-wrapper `ref_check(state)` (owns JSON-string normalization).
   `ref_check.yaml` loads it via `path:` (no imports needed).
   `persist_genesis.py` imports the sibling via a one-line sys.path shim at
   module top (`sys.path.insert(0, str(Path(__file__).parent))`) with a
   comment citing this FR — the accepted pattern; `spec_from_file_location`
   loading does not support bare sibling imports.

6. **AC-6**: (a) Existing tests pass. (b) Unit test for `ref_integrity.py`
   with list and JSON-string inputs. (c) Integration test: `ref_check`
   graph-tool invoked with orphan data returns the orphan report (mock-LLM
   agent calling the tool is sufficient). Pipeline *self-correction* is FR-685
   AC-7, not this FR.

## Implementation Approach

1. RED: test for sibling-import-free loading of `ref_integrity.py` via
   path-based tool
2. Extract `validate_referential_integrity()` → `nodes/ref_integrity.py`
   (+ `ref_check(state)` wrapper with JSON normalization + page flattening)
3. Write `ref_check.yaml`: single Python node wrapping the function
4. Add `ref_check` as `type: graph` tool in `worldgen.yaml`
5. Add `ref_check` to `deepen_events` agent tools list
6. Repoint genesis `validate` tool to `ref_integrity.py:ref_check`; delete
   `validate_genesis.py`
7. Update `persist_genesis.py` — sys.path shim + sibling import
8. Tests

## Constraints

- `ref_check.yaml` is a pure validation graph — no LLM calls.
- The graph-tool returns structured text the agent can parse.
- Does not change genesis flow shape (validate node stays; loses importlib,
  `validate_genesis.py` is deleted).
- Does not change worldgen flow (dedup node stays, ref_check is additive).

## Related

- [FR-658](FR-658-graph-as-tool.md) — enables `type: graph` tool
- [FR-664](FR-664-genesis-referential-integrity.md) — original ref integrity
- [FR-667](FR-667-genesis-stub-pipeline.md) — genesis stubs (current validate node)

## Judgement

**Verdict: APPROVED — scope frozen with amendments below.**

### Assessment

Problem is real and verified against the codebase: the importlib hack exists in
`validate_genesis.py` (lines 18–24), FR-658 graph-tools are enforced
(`yamlgraph/tools/graph_tool.py`), and `deepen_events` currently has only
`lookup_canon_page, list_canon_ids, validate_draft` (worldgen.yaml:119).
Raw-output evidence cited (zero orphans on 2026-07-04) — substance gate passes.

### Issues Found & Required Amendments

1. **AC-5 re-introduces the bug it claims to kill.** "Both `persist_genesis.py`
   and `ref_check.yaml` import from it directly" is impossible as written:
   path-based Python tools load via `spec_from_file_location`
   (`yamlgraph/tools/python_tool.py:118`) with NO sys.path entry for the tool's
   own directory. A sibling import `from ref_integrity import ...` inside
   `persist_genesis.py` fails exactly like the relative import the importlib
   hack works around. No node in `examples/novel_fandom/nodes/` performs a
   sibling import today — the constraint is real.

   **Amendment:** `nodes/ref_integrity.py` is self-contained: pure function
   `validate_referential_integrity(pages)` + state-wrapper `ref_check(state)`.
   `ref_check.yaml` loads it via `path:` (works — no imports needed).
   `persist_genesis.py` uses a one-line sys.path shim at module top
   (`sys.path.insert(0, str(Path(__file__).parent))`) before the sibling
   import, with a comment citing this FR. Document as the accepted pattern —
   it replaces per-callsite importlib gymnastics with one standard line at
   the module boundary.

2. **Graph-tool args are strings — normalize at the boundary.** FR-658
   `build_graph_tool` generates `str`-typed fields from `input_mapping` keys.
   An agent calling `ref_check(pages=...)` passes a JSON **string**, not a
   list. AC-1's graph receives `pages: str`.

   **Amendment:** `ref_check.yaml`'s first (only) node parses JSON if `pages`
   is a str, then validates. The `ref_check(state)` wrapper owns this
   normalization (the_one_law). Add to AC-1: "accepts `pages` as JSON string
   or list; normalizes at entry."

3. **AC-4 ambiguity resolved.** "graph tool call to ref_check.yaml OR direct
   Python tool call" — pick the direct path: genesis `validate` node keeps
   `type: python`, its tool config repointed to
   `path: nodes/ref_integrity.py, function: ref_check`. `validate_genesis.py`
   is **deleted in this FR** (not FR-685) — its only content is the importlib
   hack plus page-flattening, which moves into `ref_check(state)`. No
   graph-tool indirection inside genesis; that composition belongs to FR-685.

4. **AC-2 output shape.** Graph-tool returns `str(result.get(output_key))` —
   the agent sees stringified dict. Acceptable (constraint already says
   "structured text the agent can parse"), but freeze the shape:
   `{"valid": bool, "orphan_ids": [...], "violations": [...]}` rendered via
   `str()`. No prose.

5. **AC-6 test scope.** "Agent self-corrects" is FR-685's acceptance, not
   this FR's. Trim AC-6 to: (a) existing tests pass, (b) unit test for
   `ref_integrity.py` (list + JSON-string inputs), (c) integration test that
   `ref_check` graph-tool invoked with orphan data returns the orphan report.
   Mock-LLM agent test calling the tool is sufficient; "self-corrects" moves
   to FR-685 AC-7.

### Frozen Scope

ACs 1–6 as amended — **amendments folded into the AC and Implementation
sections above**. Enforce order: this FR before FR-685. TDD: RED test for
sibling-import-free loading of `ref_integrity.py` via path-based tool first.
