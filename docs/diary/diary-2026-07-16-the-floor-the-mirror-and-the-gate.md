# 2026-07-16 — The floor, the mirror, and the gate that gated its author

**Context:** FR-738 enforce — pre-commit disposition gate under the
FR-737 advisory, U-2 placement weighting, U-3 companion status.

**The recursion continues on schedule.** FR-738's own creation fired
the parent hook (four incidental hits + the parent at #1), so the FR
carries the `**Prior art:**` line its own gate now demands — the format
fixture existed before the gate did, written by the gate's author under
the gate's future law. Enforcement infrastructure that must eat its own
dogfood *before* it exists is a pleasing inversion of
`infrastructure_self_exempt`: not merely subject to the rule it
enforces, but subject to it retroactively.

**F2 earned its test immediately.** The staged-divergence case (marker
added to the working tree after `git add` → must still fail) is the
kind of pin that looks pedantic until you remember the repo's own
rhythm: hooks that auto-fix files mid-commit make "edited after
staging" the *normal* state here, not the exotic one. The gate judging
`git show :0:path` instead of the file is the difference between a
floor and a decoration.

**AC-04's prediction mechanism worked.** The judgement recorded a
falsifiable expectation — FR-070 must *improve* under placement
weighting (filename match) — and the re-measurement confirmed it: score
doubled, rank held at #2. A judgement that predicts the measurement
before the code exists converts "did the refactor break ranking?" from
a debate into a diff. Small pattern, worth repeating: every ranking
change ships with a pinned expected movement for one named fixture.

**The honest boundary is the deliverable.** F1's finding — the
motivating incident lives in a repo this gate never sees — did not
expand scope; it produced NC-394 (the mirror) and one sentence of
honesty in the README ("repo-scoped"). The alternative, folding a
cross-repo change into one FR, would have been tidier-looking and
worse: two commit streams, one concern each. `workspace_is_not_boundary`
now has a constructive corollary: when the workspace spans repos, each
enforcement floor is per-repo by nature, and the honest artifact is a
mirror FR, not a reach-across.

**Seed:** the advisory channel (PostToolUse → agent context) remains
broken and now has a floor making it non-urgent. Nothing will ever
force that investigation — the floor removed the pain that would fund
it. Is that the correct end state (boundary relocation made the channel
irrelevant), or does a deliberately unfixed channel accumulate silent
dependents until someone trusts it again? The audit log records every
firing; a quarterly grep for `feedback` events with no matching
disposition would answer whether the advisory is dead weight or quiet
value.
