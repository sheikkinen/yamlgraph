# Feature Request: FR-721 Passthrough `output` Schema Rejects Literal Seeds the Runtime Accepts

**Priority:** HIGH (blocks consumer upgrades to 0.5.11; schema lies about the runtime)
**Type:** Fix (schema/runtime contract)
**Status:** Completed
**Effort:** 0.5 day
**Requested:** 2026-07-13
**Judged:** 2026-07-13 — embedded judgement RATIFIED by independent review (see Ratification below); scope frozen.
**Spawned by:** ninchat_voice NC-370 enforce — pin alignment 0.5.7→0.5.11
surfaced `test_nc238_interrai_ca_graph_loads` failing with 8 validation
errors on a graph that runs correctly in production
**Related:** FR-673 (boundary validation — made the schema enforced),
FR-716 (graph_schema bisection — moved the field to `node_schema.py`)

## Problem

`node_schema.py` L178 declares passthrough `output: dict[str, str]`, but
the runtime contract is wider: `resolve_template()`
(`utils/expressions.py` L192–193) explicitly passes non-string values
through unchanged:

```python
if not isinstance(template, str):
    return template
```

Passthrough/init nodes legitimately seed state with typed literals:

```yaml
init:
  type: passthrough
  output:
    messages: []       # list literal
    extracted: {}      # dict literal
    has_gaps: true     # bool literal
    phase: opening     # str
```

This pattern ran in production for months. FR-673's boundary validation
made the (over-narrow) schema enforced at load; consumers upgrading past
0.5.7 now fail validation on graphs the runtime executes correctly. The
schema is the component that is wrong: it must describe the runtime, not
a subset of it. Quoting the literals in YAML is NOT a workaround —
`"[]"` is the string two-brackets, not an empty list; it would silently
corrupt state seeding.

## Proposed Solution

Widen the two fields to match the runtime contract:

```python
output: dict[str, Any] | None   # values: template str OR literal seed
outputs: dict[str, Any] | None  # alias
```

No runtime change — the runtime already implements exactly this.

## Acceptance Criteria

- [ ] AC-01 RED witness: a graph config with passthrough `output`
      containing list/dict/bool/str literals must pass
      `validate_graph_schema` — currently raises 8 ValidationErrors.
- [ ] AC-02 Template strings still validate and literal values round-trip
      through the schema unchanged (model_dump preserves types).
- [ ] AC-03 Existing schema suite green; no other field widened.
- [ ] AC-04 Changelog fragment (fix); consumer note: 0.5.7→0.5.11
      upgrades blocked on this pattern are unblocked at next release.

## Judgement (2026-07-13)

**Verdict: APPROVED — frozen as written.** Verified by the Judge:
- The runtime tolerance is not an accident: `resolve_template`'s
  signature is `template: str | Any` and the non-string passthrough is
  its documented first branch. The schema postdates the behavior.
- The alternative (make the runtime strict, literals forbidden) would
  break every deployed graph seeding state via init nodes — a contract
  break with production blast radius, rejected.
- Scope check: only `output`/`outputs` on passthrough nodes; mapping
  fields (`output_mapping` etc.) remain `dict[str, str]` — they map
  field names to field names and ARE genuinely string-only.
- The witness must use literals of all four shapes (list/dict/bool/str)
  — the bug report's exact payload (interrai_ca init node) is the
  fixture, per read_raw_output_first.

## Ratification (2026-07-13, independent review)

The FR arrived with the judgement section above already written while its
filing commit said "not judged" — the contradiction is resolved here: the
embedded judgement was re-verified adversarially and **ratified**; this
section is the authoritative grant. Additional verifications and pins:

| # | Check | Result |
|---|-------|--------|
| R1 | Schema claim | Verified: node_schema.py L178/L182 `dict[str, str]`; mapping fields (L36/40/210/213) are separate and stay string-only — scope note accurate |
| R2 | Runtime claim | Verified: expressions.py non-string first branch; control_nodes.py passthrough feeds every output value through `resolve_template` — literals flow unchanged |
| R3 | Downstream str assumptions (missed by the embedded judgement) | Linter `_extract_expression_values` already filters `isinstance(v, str)` — literals skipped cleanly; W007/E007 unaffected. No other consumer assumes str |
| R4 | Traceability (unpinned) | Tests tagged under the config-validation capability (CAP-01 family or FR-673's REQ) — exact id verified free against origin at enforce |
| R5 | Release binding | Ships next release; consumer note in fragment per AC-04 |

**Out of scope (purge list):** widening `output_mapping`/`interrupt_output_mapping`
(genuinely string→string), runtime changes, template-string syntax changes.

## Implementation (2026-07-13)

Enforced exactly as frozen. RED commit `0b192f46`
(tests/unit/test_fr721_literal_seeds.py, 3 condemned + mapping guard
green), GREEN widened `node_schema.py` `output`/`outputs` to
`dict[str, Any] | None` with descriptions naming the literal-seed
contract.

- AC-01/AC-02: interrai_ca-shaped fixture (list/dict/bool/str literal +
  template string) validates; model_dump round-trips types unchanged.
- AC-03: full fast unit sweep green (4854 passed); `output_mapping`
  guard test proves the mapping fields were NOT widened (raises
  ValidationError on non-str value).
- AC-04: fragment `changelog/unreleased/fr-721-passthrough-literal-seeds.md`
  (fix/schema, req: REQ-YG-546) with the consumer-unblock note.
- R4 resolved: REQ-YG-546 filed under CAP-01 (config loading &
  validation), verified free against origin.
- Deviations: none.
