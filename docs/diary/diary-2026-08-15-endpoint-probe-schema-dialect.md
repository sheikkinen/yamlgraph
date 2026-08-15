# Diary: FR-795 Endpoint-Probe Schema Dialect Repair

**Date:** 2026-08-15
**FR:** FR-795

## What happened

FR-785's tests proved that the endpoint-probe files and expected YAML keys
existed, but never crossed the composition boundary through
`load_and_compile()`. Once FR-794 repaired the earlier tool-manifest failure,
schema loading exposed a second defect: a native `schema:` block contained
JSON-Schema-style `type: list` and `items:` declarations.

The RED test reproduced the exact `Unknown type: 'list'` failure before the
governed prompt was changed. The authoring adapter then converted only that
prompt to `output_schema:`. The same compile test turned GREEN, and lint plus a
structured-variable smoke established that the repaired artifact works beyond
its static shape.

## Reflection

The trap was **shape-only confidence**: nineteen structural assertions made a
non-compiling graph look delivered. Each component could be inspected in
isolation while the dialect mismatch remained invisible at composition time.
The cheapest durable witness was not another YAML-key assertion but one call to
the public compilation boundary.

**Heuristic:** Every shipped example graph needs at least one test that crosses
its real loader/compiler boundary; structural tests support that witness but
cannot replace it.

**Seed:** Can the example test policy mechanically require a compile witness
for every committed graph without forcing credential-dependent execution?
