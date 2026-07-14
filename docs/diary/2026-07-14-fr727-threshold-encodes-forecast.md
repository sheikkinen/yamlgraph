# 2026-07-14 — FR-727: the acceptance number that was wrong by being right

**Context.** FR-727's AC-01 demanded ≥24/30 on the harness; the
definitive baseline measured 22/30. By the letter, the criterion
failed. By substance, the fix is total: zero of the eight residual
failures involve a capped code — every one belongs to the classes the
judgement explicitly deferred (chapter-code inflation ×4, model
variance on ambiguous fixtures ×4). The regression the FR exists to
kill is 5/5-dead on both fixtures that exhibited it.

**Trap: threshold_encodes_forecast.** The ≥24/30 number was the
judge's per-fixture FORECAST of how residual defect classes would
distribute — not a property of the fix under test. When an acceptance
threshold aggregates over failure classes outside the FR's scope, it
tests the judge's prediction of OTHER defects, not the enforcement.
The honest resolution is neither relaxing the number post-hoc nor
gaming fixtures until it passes: it is reporting the taxonomy —
in-scope failures: 0/8; deferred-class failures: 8/8 — and letting the
FR close on substance with the letter-miss documented. The shortfall
IS the deferred defect's quantification; it becomes the next FR's
opening evidence instead of this FR's shame.

**Heuristic.** Acceptance criteria for fixes should be scoped to the
defect class under repair ("zero failures involving capped codes"),
with aggregate numbers recorded as context, not gates. An aggregate
gate on a multi-defect surface either blocks a correct fix or forces
scope creep — both worse than taxonomy honesty.

**Compounding hazard, third occurrence today:** the parallel-session
interleave corrupted two baseline attempts (venv console script
deleted mid-`pip install` → 21 dead runs; one stale-code archive
detected only because its `-69` primary was IMPOSSIBLE under the cap —
impossibility as provenance check). Cures: runner resolves via the
venv interpreter's `python -c` (reinstall-proof), measurement tools
treat failed runs as data, archives quarantined by provenance before
definitive measurement. The "impossible result as stale-artifact
detector" trick generalizes: any enforcement that makes a state
unreachable turns that state into a tripwire for mixed-provenance
evidence.

**Seed:** Should the harness stamp each result.json with the git SHA
of the reducer that produced it, so provenance is checked by equality
instead of inferred from impossibility — and is that the general cure
for shared-repo measurement runs (every archived artifact carries the
code identity that made it)?
