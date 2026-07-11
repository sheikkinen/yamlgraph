# The Witness That Guarded Its Own Grave

**Date:** 2026-07-11
**FR:** FR-713 Part B (uniform cache, env fingerprint)
**Insight:** the cleanest RED is an existing test asserting the world you
are about to retire — and it bites the hand that inverts it

## What happened

Part B's RED was not written; it was found (F15). The FR-712 unit gate
already asserted the old policy with precision: `first is not second` for
google/vertex, `_UNCACHED_PROVIDERS` present in source. Inverting it gave
condemning tests whose failure messages were already field-calibrated.
Then the inverted witness immediately caught its own author: my GREEN
kept the string `_UNCACHED_PROVIDERS` in a history comment ("...retired
the FR-712 _UNCACHED_PROVIDERS carve-out"), and the source-scan assertion
failed on the commemoration of the thing it forbids. The carve-out was
dead but its name still occupied the module — the witness refused the
distinction, correctly: entropy includes the residue of deleted code, and
a source-level ban is a ban on the *token*, which is what keeps future
`git grep` archaeology honest.

Second finding of the day, same organ as Part A's: REQ-YG-540's rewrite
(F16) had to route around the changelog cross-wiring gate — FR-712's
unreleased fragment already claims that REQ, and the gate correctly
forbids a second FR claiming it. The fragment ledger is append-only
history; the requirement registry is mutable present. Part B's fragment
claims REQ-YG-541 (its own capability) while the REQ-YG-540 *text*
evolved in place. Ledger and state, not two states.

## Heuristic

Before writing a RED for a policy inversion, grep the suite for the tests
that enforce the current policy — they are the RED, pre-calibrated, and
deleting-by-inverting them guarantees no orphaned witness keeps guarding
the retired world. And when a source-scan witness fails on a comment:
the comment loses. Commemorate deleted special cases in the FR and the
diary, never in the module that finally got clean.

**Seed:** the fingerprint var lists in `_PROVIDER_FINGERPRINT_VARS`
duplicate knowledge the constructors in `llm_providers.py` hold
implicitly (which env vars each reads). Could a constructor declare its
env dependencies (a `reads_env` attribute) so the fingerprint derives
from the declaration and a new provider cannot silently ship an
unfingerprinted env dependency?
