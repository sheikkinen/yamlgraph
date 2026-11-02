# Diary — FR-1155: The Vendor Blog Post That Became a Node Type

**Date:** 2026-11-02
**Arc:** research note → examples census → native-sample proposals →
feasibility probe → FR-1155 → judge → enforce (decision node +
calibration audit + smart-if), all on one branch, one session.

## What happened

A "research this URL" request compounded, step by honest step, into a
shipped framework primitive. The pivotal moves were all *reads*, not
writes: reading the examples corpus revealed that decision-shaped nodes
are hybrids (enum + reasoning string); reading the vendor's docs revealed
a public adapter that made the interface buildable today; reading ten raw
adapter responses revealed that `noul` carries no confidence field and
that the adapter *derives* confidence from probabilities with two exact
formulas — facts that rewrote the FR's contract table before any code
existed. The judge then weaponized the repo's own law against the FR:
`read_raw_output_first` applied to a plan that merely *scheduled* the
reading. Correct verdict. The ten samples cost twenty minutes and changed
three design decisions.

## The trap I want to name

**The completeness-gate cascade is the feature, not the friction.** One
new enum member (`NodeType.DECISION`) tripped twelve distinct gates:
enum-census tests, registry-coverage tests, loop-limit classification
(with its "a new type must be classified before it can ship" docstring),
module-size splits (two, forced at 400 and 450), module-map budget,
vulture whitelist, noqa and hedging allowlists whose *line numbers*
shifted, README audits, demo-proof logs. Every failure was my change's
responsibility, and every gate knew it before I did. The near-trap was
reading this cascade as noise to be silenced rather than as the system
enumerating exactly what a new node type owes. Boring enforcement —
the judgement was good, so nothing in enforcement surprised more than
the gates themselves.

A second, sharper catch: the **sole route found my bug**. The first
author.sh run failed on a retired model pin (fix the adapter, never
bypass), and the second run's honest validation record reported that the
linter's hard-coded `VALID_NODE_TYPES` omitted `decision` — a gap my own
28-test suite missed because I tested config validation, not the lint
registry. The authoring agent, forced to lint, could not not-find it.

## Heuristic

When adding a member to a closed enum, grep for the enum's *name* across
tests and classification modules before running anything — the census
tests ARE the checklist of what a new member owes. And: line-pinned
allowlists (noqa confessions, hedging ALLOWLIST) are tripwires on any
edit above them; budget one shift-fix round per file you touch near the
top.

## Seed

**Seed:** The calibration-audit demo plants its miscalibration; the real
event fires when Jev access arrives. What would it take for the audit to
run against `system_one_adapter` with a *labeled public corpus* (e.g.
the CWE classifier's hand-labeled set) so the first real reliability
table exists the day a key does — and should the adapter-derived
confidence formulas (peak-rescale for choice, MAD-from-mode for score)
be audited separately from a native model's emitted confidence, since
they are different epistemic objects sharing one field name?
