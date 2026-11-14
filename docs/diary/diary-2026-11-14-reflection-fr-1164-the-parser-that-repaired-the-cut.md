# FR-1164: The parser that repaired the cut

**Date:** 2026-11-14
**FR:** FR-1164 (raise `OutputTruncatedError` on output-limit stops)

## What happened

The operator saw empty answers from a map whose items had a small
`max_tokens`. The obvious story was thinking eating the budget, and that
story is real. But the paid probe ran with no thinking at all and found a
worse case: under constrained decoding, Haiku stopped at 16 tokens mid-array,
the library's partial-JSON parser closed the brackets, and `invoke_structured`
returned `Countries([..., 'Angola', ''])` — a valid model with an invented
trailing element. The stop reason lived only on the raw message, which the
binder discarded before anyone could look.

## Trap: plausible_wrong_answer, produced by a helper

Helpful repair at one layer destroys the signal the next layer needs. A
parser that "tolerates" truncated JSON turns a provider's honest
`stop_reason=max_tokens` into a success. The shape check passes because the
repair was designed to make it pass.

## Heuristic

When a library repairs malformed output, the completeness signal must be
read from the raw reply *before* the repair, at the boundary that still holds
it. Ask for the raw envelope (`include_raw`) wherever correctness depends on
metadata the parsed form drops.

**Seed:** Which other library conveniences in the LLM path (partial-JSON
parsing, `extract_json` returning text unchanged, content normalization
dropping non-text blocks) discard a signal that some later failure needs?
An inventory of "lossy normalizers" × "the metadata each one drops" would
show where the next silent success hides.
