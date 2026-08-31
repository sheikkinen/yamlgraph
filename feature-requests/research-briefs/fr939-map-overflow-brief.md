# Problem brief: map fan-out overflow is silently truncated and reported as success

**Prior art:** the execution-safety guards FR
(`feature-requests/027-execution-safety-guards.md`) introduced the cap
deliberately as truncate-and-warn — the contract under examination
here, at the scale it was designed for (default cap 100, small demo
graphs). FR-936
(`feature-requests/FR-936-map-node-hardening.md`) bundled this concern
with three others and was SPLIT by its judgement
(`feature-requests/FR-936-map-node-hardening.judgement.md`,
R-4/AC-05/AC-06); this brief is that judgement's deliverable D-2 and
inherits its scope fence: timeout lifecycle
(`feature-requests/069-map-node-timeout.md`, D-3), input projection
(D-1), and native retry (D-4) are adjacent but out of bounds.
`capabilities/CAP-11-subgraph-map.yaml` is the governing capability. A
REJECTED-FR sweep found no prior proposal governing overflow
disposition specifically.

## Problem statement

The map node caps fan-out at `max_items` (node-level) falling back to
`max_map_items` (graph defaults) falling back to
`DEFAULT_MAX_MAP_ITEMS = 100` (`yamlgraph/config.py:57`). When the
resolved `over` list exceeds the cap, `map_edge` logs a warning, slices
the list, dispatches Sends for the surviving prefix, and the run
completes with success status (`yamlgraph/compile/map_compiler.py:350-365`).
Nothing in the returned state, exit code, or result records that items
were dropped; the warning line in the log is the only witness, and it
does not survive into any artifact.

At the design scale of the original guard this was a cost guard against
runaway demo
graphs. At production scale it is silent data loss: a map over 500,000
items with the default cap produces a result computed from 100 items
and reports it as complete. The consumer cannot distinguish a truncated
run from a full one without reading logs. This is the
`plausible_wrong_answer` trap in the Scripture's terms, and it sits in
tension with Commandment 6: "Thou shalt not hedge with silent
fallbacks; when a filter yields nothing, raise — never substitute
everything." The truncation here substitutes a prefix and stays silent
in-band.

The test suite pins the current behavior as expected
(`tests/unit/test_fr027_execution_safety.py`), so today the wrong
contract is protected by a witness.

The problem: overflow disposition is not a configurable, observable
contract. There is exactly one behavior (truncate, warn out-of-band,
succeed), it is wrong for at least one named consumer class, and no
YAML surface exists to select anything else.

## Classification

enforcement/latency-critical

## Constraints

- The FR-936 judgement scope fence applies (C-1, C-6): this concern
  ships alone — no timeout, retry, payload-projection, durability, or
  chunked-scheduling changes ride along.
- The execution-safety guards FR's contract
  (`feature-requests/027-execution-safety-guards.md`) must be
  explicitly superseded or preserved with rationale, not silently
  drifted (it records truncate-and-warn as a decision, not an
  accident).
- Both configuration levels must keep working: node-level `max_items`
  and graph-level `defaults.max_map_items`.
- Whatever the disposition on overflow is, it must be decidable and
  surfaced BEFORE the first sub-node executes — an overflow discovered
  after spending 100 LLM calls has already paid the cost the cap
  exists to prevent.
- Any error surfaced must identify the node name, the observed item
  count, and the configured cap (actionable without log archaeology).
- Invalid configuration values must be rejected at graph
  load/validation time, not at fan-out time (Commandment 3: config is
  truth, validated).
- Existing graphs that rely on capped execution as a deliberate
  sampling/cost device must remain expressible — the capability may
  not simply be deleted.
- Typed schema surface (Pydantic, Commandment 5); no stringly-typed
  pass-through.
- The witness tests must cover: node-level cap, graph-default cap,
  within-cap input (no behavior change), and each supported overflow
  disposition, with the RED committed before the fix (Commandment 7).
- `is_this_a_graph`: must be answered in the research — this is a
  compile-time contract change inside the framework, but the research
  route itself should confirm no graph-shaped alternative is being
  missed.

## Witnessed incidents

- 2026-08-31 FR-936 audit: `map_compiler.py:350-365` truncate-and-warn
  confirmed against current source; judgement verified the slice
  happens after a shallow full-state copy is already prepared for every
  surviving Send.
- `docs/plan-web-toolkit.md` (rev 8-10): the fi-catalog pilot (component
  D) is the named first consumer — a ~500k-domain map where silent
  truncation produces a silently incomplete national catalog while the
  run reports success. D is sequenced behind this fix.
- `tests/unit/test_fr027_execution_safety.py` asserts truncation as
  correct behavior — the regression suite currently defends the defect.
- FR-936 judgement AC-05/AC-06 record the acceptance shape its judge
  considered mechanically enforceable for this concern; preserved here
  as input, not as a foregone conclusion.
