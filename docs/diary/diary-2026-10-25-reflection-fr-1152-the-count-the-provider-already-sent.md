# Reflection: FR-1152 — the count the provider already sent

**Date:** 2026-10-25
**FR:** FR-1152 (`--token-usage` counts thinking tokens)

## What happened

The first consumer, game-engine's stage 5, needed "tokens, thinking tokens and dollars per step". Its earlier
graph estimated thinking by subtraction: output tokens less the answer's length over four. The provider already
sends the exact number, and LangChain already normalises it into `usage_metadata.output_token_details.reasoning`;
the tracker simply never read it. One field and a suffix fixed it.

The judge found what the FR had not said: that the count is inside `out`, not beside it (a reader would add 568 to
701); that two tests compared `summary()` whole and would turn red; that a `None` would raise inside a callback,
mid-run; and that every cited sample had thinking at zero, so nothing showed the path working. The live witness
answered the last one with 603 reasoning tokens.

## Root cause

A number estimated by a consumer is a number the boundary did not pass on. The estimate was written because the
tracker was trusted to report what there was.

## Heuristic

**Before estimating a quantity downstream, look for it in the normalised payload at the boundary.** If it is there,
pass it on; an estimate is a bug report about the boundary.

Second: **a witness at zero proves nothing about a counter.** Pick the input that makes the count move.

## Corrective actions

- `total_reasoning_tokens` in the tracker; `, N thinking` on the printed line when N > 0.
- The live witness pasted in the FR.

**Seed:** Should `--json` carry the token usage too, so a runner reads numbers instead of parsing a console line?
