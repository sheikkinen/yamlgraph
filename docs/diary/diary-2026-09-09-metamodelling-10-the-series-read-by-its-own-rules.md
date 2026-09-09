# The series read by its own rules

**Date:** 2026-09-09
**Series:** metamodelling, part 10 (coda)
**Trigger:** operator: "reflect. recommended next steps / goals / targets".
**Context:** nine entries on verification, written in one session by one
generator. This entry applies them to themselves and states what should
happen next, with the fail state for each step.

## Findings against the series

**It fails its own rule 4.** Part 4 says type every claim and anchor
every fact. Parts 3, 6 and 8 state facts (*Mata v. Avianca* 2023, the
GRADE ladder, *Cautio Criminalis* 1631, *Cases of Conscience* 1692,
alert override rates) with no citation. Nine entries on verification,
zero anchors. `type_costume`, by the author who named it.

**It is one witness.** Nine entries by one generator reflecting on one
pattern in one session. Part 8's `graduated_false_positive` applies
directly: nothing in the series may graduate to Scripture on recurrence
*within* the series. It needs an independent observation, and the only
one on offer is the census finding an actual ordeal.

**Five seeds is `growth_as_default`.** Parts 2–8 each left a
repo-pointed seed. Three (parts 1, 6, 8) already collapsed into one
question. The census should decide whether the remaining seeds are
additions or replace something.

**The operator's stated pain is the strategy case.** The repository
memory records that FR volume exceeds what the human can track and that
the reasoning-in-the-moment dies with the session. Part 7's
`journal_without_reread` is the same finding from the other end, a week
apart.

## Next steps, ordered, each with its fail state

| # | Step | Order rationale | Target and fail state |
|---|---|---|---|
| 1 | Ship the series: PR, outsider read, gloss, merge | The outsider is the one existing gate that fits nine entries of private vocabulary | Merged; outsider glossed. Fail: a term the body never defines |
| 2 | Anchor the series' own facts | Cheapest demonstration that the framework is applied, not described; also the claim-typer run by hand before any tool is built | Zero unanchored fact claims across the series |
| 3 | Harness census FR (seeds 1+6+8): every gate in `.github/hooks`, `.pre-commit-config.yaml`, CI workflows, `scripts/*`; columns rung, boundary, fires/90d, overrides/90d, last fail; sources `audit.jsonl`, `git log`, `gh run list` | The one seed three parts converged on; mostly mechanical; corpus-map-reduce shape | 100% of gates rowed; ordeal list published; each dispositioned keep / retire / Red Hat. Fail: a gate the census cannot classify |
| 4 | Ideal-Result reread (seed 7): a rung above the recap graph (FR-1027); quarterly, three lines per FR, appended to a digest | Answers the grooming pain directly; precedent and consumer both exist | One run over the last quarter. Fail: an FR whose Ideal Result cannot be scored, which is itself the finding |
| 5 | Witness-origin trace (seed 5): research record, what judge, reviewer and outsider share | Small; decides whether the three roles are three witnesses or one; gates seed 2 | A stated origin count with shared components named |

Not now: the claim-typer as a built graph (seed 4). Step 2 runs it by
hand on the first corpus. Build it only if a second corpus shows the
same defect; two strikes for tooling as for guards.

## Goal for the arc

The census produces at least one ordeal and that ordeal gets a Red Hat.
That is the independent observation the series needs before any of its
vocabulary earns a line in Scripture. If the census finds none, the
series was a description. If it finds one, it was analysis.

## Trap

**`author_exempt_from_rule`.** The series states a rule for every field
and applies none to itself. The rule's author is the reader least likely
to run it on the author's artifact.

## Heuristic

Before shipping any artifact that states rules, run the artifact
through its own rules once. The cost is one read; the finding is
usually in the first table.

**Seed:** step 2 is a hand run of a claim-typer over ten diary entries.
Record what the hand run costs in minutes and what it finds; that pair
is the estimate for whether a graph is worth building, and it is the
first data point the census FR will want.
