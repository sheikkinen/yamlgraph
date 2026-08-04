# The Guard Met Its First Stranger

**Date:** 2026-08-04
**Context:** Asked to "check latest manifest feature" — the FR-768..FR-772
tool-manifest arc, authored entirely in other sessions and merged today. I am
the session that built FR-767's authoring sole-route guard five days ago;
this is the first arc that ran under it without me in the room.

## What the record alone could reconstruct

Input closure works in reverse. Without any chat narrative from the authoring
sessions, the artifacts reconstructed the entire arc: five judged FR pairs,
RED/GREEN commit separation in `git log`, the measured problem statement
(333 declarations, 26 duplicated signatures — a scan script, not an
assertion), `demo-output.log` proving execution, and two diary entries naming
the traps as they happened. Verified live in this session: demo graph lints
clean, 20 manifest unit tests green. A successor with amnesia needed about
ten reads to know *what happened and why* — that is the traceability spine
doing its job, and it is worth saying out loud because the alternative
(archaeology through chat logs) is what every other project does.

## The denial that mattered

`audit.jsonl` shows 46 `authoring-route` denials since the guard shipped:
45 on 2026-07-29 — construction day, my own self-tests and the guard denying
its own author — and exactly **one** on 2026-08-04: an `apply_patch` write to
`examples/demos/shared-vision-tool/graph.yaml`, denied mid-arc in a foreign
session. The sibling diary confirms the aftermath: the demo went through
`author.sh`, and the route surfaced an ambient `PROVIDER=azure` conflict the
direct write would have shipped.

The trap this exposes is **denial-count homogeneity**: reading "46 denials"
as one number. Construction-day denials are calibration — the mechanism
proving it can fire. A foreign-session denial is *evidence* — the mechanism
firing at someone who didn't build it, wasn't thinking about it, and had an
editor-shaped write ready to go. One field catch outweighs 45 self-tests.
When auditing whether a guard "held," partition denials by session
provenance before counting.

## The interlock nobody planned as an interlock

FR-768's AC-09 (migrating the chaplain trio's byte-identical toolkit blocks
to manifests) is explicitly *gated on the graph-authoring route*. Two
mechanisms enforced five days apart now form a closed loop: the reuse
primitive (manifests) can only reach governed graphs through the sole route,
and the sole route's adapter is itself the thing that will perform the
migration. Enforcement infrastructure became load-bearing for feature
rollout within a week of shipping — `boring_enforcement` in its best form:
nobody had to decide this; the constraints composed.

Design note for the record: `manifest.py` is `the_one_law` verbatim —
validation and translation at the graph-load boundary, `extra="forbid"` on
every model, name-match check against the tool key, absolute-path resolution
at translate time, and byte-for-byte inline-shape output so zero downstream
code changed. The FR's "no new execution engine" constraint is what kept a
2-day feature 2 days.

## Heuristic

A guard's proof of value is its first *foreign* denial, not its test suite
and not its construction-day firings. Partition audit events by provenance
(builder session vs. stranger session) — the second population is the only
one that measures deterrence of anyone but the author.

**Seed:** The audit trail records denials, but route *compliance* is
currently proven by inference — absence of denial plus presence of a
`draft-authoring-report.md`. Should the guard also log ALLOW events for
sentineled writes to governed paths, so "the route was used" becomes a
positive first-party record instead of a negative-space deduction? An
allow-log would also expose the base rate: one denial per how many
sanctioned writes?
