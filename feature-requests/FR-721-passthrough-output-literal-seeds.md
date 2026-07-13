# Feature Request: FR-721 Passthrough `output` Schema Rejects Literal Seeds the Runtime Accepts

**Priority:** HIGH (blocks consumer upgrades to 0.5.11; schema lies about the runtime)
**Type:** Fix (schema/runtime contract)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-07-13
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
