# The Record That Contradicted Itself

**FR-526 — DM v2 close-seam lifecycle coherence invariant**

## What happened

FR-526 began life as a wrong fix for a real symptom. Its original draft assumed a
chapter that force-closed mid-reversal *dropped* the promised return on the floor, and
proposed to forward it as an `open_threads` dict. The judge killed the mechanism on
contact with the live schema — `open_threads` is `list[str]`, and `parse_seam_packet`
drops every non-string entry, so the dict would vanish at the seam — and demanded an
`investigation_before_fix` probe before the FR earned any scope.

The probe paid for itself. A pure read-only read of the real `10024-BC` story.json
showed the premise was false: a lifecycle forward *was* already emitted. But it was
**incoherent**. Ch3 committed Arnulf as `existence_state=confirmed_dead` AND
`allowed_reappearance_from_chapter=3` — a confirmed-dead actor *allowed to reappear*,
from the very chapter he died in. The defect was never a missing record; it was a
self-contradictory one. The fix re-scoped to a pure, packet-only coherence invariant
at the close seam: a non-null reappearance allowance softens `confirmed_dead` to
`missing_presumed_dead`, preserving the authored return intent.

## The trap

**`vendor_default_as_help` inverted into `downstream_fix` — proposing a NEW channel
for data the system already carried.** The original FR reinvented `CharacterLifecycle`
(badly, as an untyped dict) because it never checked what `close_chapter` actually
emitted. It pattern-matched "promise lost" and built a forwarding mechanism for a
forward that already existed. The cheapest refutation was not an argument — it was one
`json.load` of the committed artifact. The assumption survived only as long as nobody
read the file it described.

## The insight

A clamp that reconciles *one* facet of a record silently certifies the rest. The
existing `_clamp_lifecycle_reappearance_to_plan` raised the reappearance *index* to the
planned chapter and returned the row looking handled — but it never touched
`existence_state`, so an incoherent state/allowance pairing rode straight through. The
cure is a separate, single-responsibility invariant: the clamp owns the index (and
needs the `doc` to find the plan), the coherence invariant owns the state (and needs
only the packet). Splitting them by what-they-depend-on keeps each pure and each
testable in isolation — and makes the seam, not a downstream consumer, the place the
record is made coherent (`the_one_law`).

The structural read: **two facets of one record, reconciled by two different concerns,
will drift unless something asserts their joint coherence.** `confirmed_dead` and
`allowed_reappearance` are individually valid and jointly nonsensical; no per-field
validator catches a cross-field contradiction. The invariant is exactly that missing
cross-field assertion, normalized where the record is committed.

## The method that paid off

Condemn a REAL record, not an imagined one. The RED fixture mirrors the exact
`10024-BC` Ch3 shape, so the test is a forensic reconstruction of a production defect,
not a hypothesis. The required non-vacuous negative control (a genuine `confirmed_dead`
with a `None` allowance stays dead) guards against an over-broad fix that would
resurrect every villain. And the J6 integration assertion is non-vacuous by
construction: it feeds the reconciled seam to the cross-source memory-precedence gate
with a synopsis state that would *mismatch* a `confirmed_dead` seam — so the test fails
if the coherence fix is removed, proving the fix actively prevents a downstream
conflict rather than merely passing alongside one.

**Seed:** FR-525's witness and FR-526's invariant both encode the same domain truth —
"a character the plan returns is not confirmed dead" — at two different boundaries
(outline-time pack detection, close-time record coherence). When the same rule is
enforced at N boundaries by N independent checks, is the rule itself a candidate for a
single shared predicate they all import, and would a divergence between those N
encodings be a defect worth its own gate?
