# Reflection: FR-1120 — the order nobody specified

**Date:** 2026-09-27
**FR:** FR-1120 (census map memo)

## What happened

AC-06 asked for the memo reducer path to write JSONL byte-identical to
the live path. The witness passed for everything except order: the live
path emitted rows in findings-then-failures order, which is the order the
map's two output channels happen to be concatenated. Nobody chose that
order; it fell out of `[*findings, *failures]`. The memo path, rebuilding
from one index-keyed record set, naturally produced index order.

A byte-identity criterion made an unspecified property visible. The fix
was to specify it (sort by `source_index`) on both paths, not to mimic
the accidental order in the new path.

## Trap

`accidental_contract`: an equality witness between two implementations
surfaces properties that neither spec states. The reflex is to make the
new implementation reproduce the old accident.

## Heuristic

When a byte-identity test fails on ordering, ask which order a reader of
the artifact would expect, fix that order in both paths, and record the
change as a deviation. Replicating an accident freezes it.

**Seed:** Which other census/ledger artifacts carry an order that is
really the concatenation order of map channels, and would a
`sorted_by_index` assertion in the FR-1073 contract tests catch them all
at once?
