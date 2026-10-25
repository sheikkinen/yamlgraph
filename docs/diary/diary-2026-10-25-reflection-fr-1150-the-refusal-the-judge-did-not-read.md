# Reflection: FR-1150 — the refusal the judge did not read

**Date:** 2026-10-25
**FR:** FR-1150 (split `llm_providers.py` under the size gate)

## What happened

`llm_providers.py` was 473 lines, held by FR-1149's temporary entry. The first plan moved two blocks: the
thinking-off rule, which FR-1148 had named for its own module, and the FR-998 capability predicates, re-exported
from `llm_providers`. Round 1 of the judge approved it with nine revisions, among them a repair to FR-998's
locality test, which the re-export would have passed by shape alone.

Folding that revision meant reading FR-998, which shows its review #599 P2 had already refused this exact move:
the predicates had been put in a new module once, called "source-of-truth drift", and frozen in `llm_providers`;
the cure then was to move other code out. The round-1 judgement read FR-998's test and missed FR-998's decision.
The plan changed: the Anthropic factory, the rule's only caller, moves with the rule, and the predicates stay.
Round 2 approved with five small revisions. One of them found a line-keyed confession (CONF-352) that the move
would shift by fifty lines; the probe showed it already points at nothing.

The move is byte-identical to the anchor; the size gate's honesty test, whose last clause was always true, now
fails on any entry at or under the limit, and the RED witness shows it failing on the very entry this FR removes.

## Root cause

A move-only split looks free of history, so its research stays inside the file being split. The constraint that
mattered was a decision recorded in another FR's review, about where code *must* live, and nothing in the file or
its tests carries it: the test checks presence by `getattr`, which a re-export satisfies.

## Heuristic

**Before moving code out of a module, read the FRs whose names are in its docstring and search their reviews for
"live in", "frozen", "boundary".** A location can be a decision, not an accident; the test that guards it may
check only that the name resolves.

Second: **a gate's honesty test needs a clause that can fail.** `actual > LIMIT or allowed >= actual` after
`actual <= allowed` is a tautology; a stale entry stayed invisible until a test was written to fail on one.

## Corrective actions

- The thinking rule and the Anthropic factory in `anthropic_thinking.py`, byte-identical; old names re-exported.
- The honesty test asserts `actual > LIMIT`; FR-1149's temporary entry removed.
- The dead CONF-352 entry, and the gate's blindness to a stale ALLOWLIST key, parked for a separate FR.

**Seed:** Should a module's "frozen location" decisions live in the module itself (a docstring line or an
import-linter contract) so that a split meets them where it starts, instead of in a review three FRs away?
