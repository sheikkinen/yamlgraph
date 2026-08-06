# The Envelope That Ate the Error Message

**Date:** 2026-08-06
**Context:** FR-778 (tool_call `on_error: fail`) — from a witnessed field
failure to a judged, enforced framework primitive in two sessions. Includes
the FR-776→FR-778 ID-collision renumber (race recurrence #4).

## The arc

Running the book-summary demo on a fresh machine without poppler produced the
purest specimen of `downstream_fix` I've seen: the splitter raised "pdfinfo
not found" — a perfect error — and `tool_call`'s catch-all converted it into
a success-shaped envelope that nothing was forced to check. The run died
three nodes later inside the map with "cannot resolve chunks". Two correct
components, one silent policy between them: the composition_bug shape, again.

The judge added real value beyond ratification: it found that the generic
node schema accepts any `ErrorHandler` value while only the *linter* flags
unsupported ones on non-LLM nodes — so my "reject at graph load" AC was
quietly unimplementable as written without touching the schema layer. R-1
turned a vague criterion into a mechanical one.

## Implementation trap worth keeping: validator ORDER is contract surface

AC-04 required every invalid `on_error` on tool_call to name the valid set
`skip, fail`. My first implementation put the check in the `mode="after"`
model validator — but Pydantic field validators run first, so arbitrary
values ("explode") died at the generic field validator with the full
ErrorHandler list, while `retry`/`fallback` (valid ErrorHandler members)
passed through to my check. The message a user sees depended on WHERE in the
validation pipeline their typo fell. Cure: `mode="before"` validator — the
type-specific rule must outrank the generic one, and in Pydantic that
ordering is expressed structurally, not by code position.

## The ID collision, again

My FR-776 collided with a parallel session's FR-776 (vision fallback) that
landed origin-first and fully enforced. Renumbered mine to FR-778 per the
FR-731 precedent. The sharpened lesson (now in repo memory): the `uniq -d`
duplicate check must run at PUSH time, not allocation time — the collision
formed in the hours between my allocation and my push while origin advanced
six commits. And the rebase conflict on fr-board.md WAS the tell; I resolved
it mechanically without asking what caused it. A conflict in a generated
file is a message about parallel work, not just noise to regenerate away.

## Heuristic

When a node type wraps failures into data (envelope pattern), the wrap is a
POLICY with two legitimate consumers pulling opposite directions: agent
loops need error-as-text, pipelines need error-as-stop. If only one policy
is expressible, the other manifests as bugs at a distance. The fix is never
"pick the right default" — it's making the policy a declared, load-validated
choice.

**Seed:** `tool_call` now has skip/fail. The `map` node's `on_error: skip`
has the same two-consumer split (silent item omission vs fail-fast — FR-044a
territory, still unresolved years later). Should every error-swallowing
boundary in the framework be audited for "is the swallow a declared choice
or an accident of implementation"?
