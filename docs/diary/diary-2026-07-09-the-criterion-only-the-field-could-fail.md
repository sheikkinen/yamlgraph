# The Criterion the User Added Was the Only One That Could Fail Honestly (FR-704)

**Date:** 2026-07-09
**Context:** FR-704 enforce — orphans evicted from the model; the user added a field-rerun acceptance criterion before granting enforce.

## What happened

FR-704's unit criteria were all guaranteed-green by construction: once orphans
are a list copy in Python, "hash arrives bit-exact" cannot fail in a fixture.
The tests condemn the *old* design but cannot interrogate the new one — a
for-loop does not flake. The user's added criterion — rerun against
ninchat_voice and mechanically resolve every orphan hash via `git cat-file` —
was the only acceptance gate exercising the change against reality rather
than against its own definition.

And it delivered a finding the fixtures could not: all 11 hashes resolved
(criterion PASSED, corruption extinct), but the window rule flagged 7
convention orphans because ninchat_voice has no `changelog/unreleased/`
directory at all. The rule as frozen (J3) treats "convention absent" and
"convention violated" identically. Frozen-correct, field-noisy — recorded in
the FR as a follow-up candidate rather than silently widened in scope.

## The insight

For mechanization FRs, unit tests verify the mechanism but the mechanism is
trivially correct; the risk lives in the *policy* the mechanism encodes
(which window, which paths, which absence means what). Policy defects are
invisible in fixtures authored by the policy's author — they surface only
against a repo the author didn't shape. The field rerun is to policy what
the failing test is to code: the only witness that can say no.

## Heuristic

Every FR that moves work from model to code should carry one acceptance
criterion that runs the whole pipeline against a real, foreign corpus and
asserts mechanically. Unit fixtures prove the transport; only field runs
prove the policy. (Corollary of `read_raw_output_first` — here the read was
mechanized into the criterion itself: a verification loop, not an eyeball.)

**Seed:** The convention-orphan rule needs a three-state boundary: convention
absent (directory missing at HEAD) → no entries; convention present but
window fragment-less → flag; fragments present → suppress. Should
"convention detection" become a dedicated deterministic state key that all
convention-dependent rules consult, instead of each rule inferring absence
from empty strings?
