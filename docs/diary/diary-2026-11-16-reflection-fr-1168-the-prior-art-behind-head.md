# Reflection: FR-1168 — the prior art behind `head`

**Date:** 2026-11-16
**FR:** [FR-1168](../../feature-requests/FR-1168-pages-liquid-gate.md)

## What happened

GitHub Pages had failed on every push for weeks. One investigation note quoted
`{{ <key>` in a code span. Liquid runs before Markdown, so code spans are no
protection, and an unterminated `{{` is a fatal parse error. The first draft of
the fix was narrow: flag only the token shapes that break the build. The judge
found FR-751, an unjudged proposal from months earlier that had already argued
for the strict rule. My prior-art search had matched it, but I piped the result
through `head`, and FR-751 was the eleventh line. Measuring the strict rule
then showed what the narrow rule would have missed: 23 balanced tokens,
including six `${{ secrets.* }}` lines in a published workflow example. Jekyll
built them without complaint and rendered them as empty text. The last green
Pages build already had 21 of them.

## Trap: truncation as a silent filter

`head` is a display convenience, but in a search it decides what exists.
A prior-art grep that shows the first ten matches answers "is there prior art
in the first ten?", and the answer looks like a full answer. The truncated
line carried the strict proposal, and the strict proposal carried the bigger
defect: silent text loss, which no build failure would ever report.

## Heuristic

For any search whose absence of results drives a decision (prior art,
references, callers), count before you view: `grep -c` or `| wc -l` first,
then read all of the matches or page through them deliberately. A green build is
not evidence of correct output when the renderer turns bad input into empty
text.

## Seed:

Should the prior-art hook print the total match count alongside its excerpt,
so a truncated view announces that it is truncated?
