# The sample that named its own bugs

*FR-495 (chapter heading dedupe) + FR-496 (cast lines leak the SUMMARY sheet)*

## What happened

FR-494 gave the Dungeon Master prototype a pure, no-LLM full-story render. The
tests were green, the gates clean, the abstraction sound. Then I ran it for real
on a live story and read the output as a human would. Two defects fell out of the
prose that no unit test had asked about:

1. `# Chapter 1: Chapter 1 — The Frozen Crossing` — the LLM's title self-asserted
   its own ordinal, and the composer, which already owns the ordinal `n`, stacked
   a second one on top.
2. `- **Kaelen Vance** — SUMMARY: A military courier… ROLE: … ORIGIN: …` — the
   cast bullet leaked the entire character sheet, because the sheet is a single-
   `\n`-separated labeled block and the FR-494 gloss was `split("\n\n")[0]`, which
   on a sheet with no blank lines returns *everything*.

Both became FRs, both were judged with frozen scope, both enforced here under TDD.

## The trap: the demo is a boundary the tests did not cover

The unit suite proved the *contract I imagined* — order, suppression of the
world-state ledger, the raise on an empty book. It could not prove the contract I
*didn't* imagine: that an LLM would helpfully prepend "Chapter 1 —" to a title, or
that a character card is a label sheet and not a paragraph of prose. The fixtures
encoded my mental model of the data; the live run encoded the model's actual
output. The gap between them is exactly where both bugs lived.

This is `plausible_wrong_answer` wearing a green suit. The render passed every
shape check — it produced valid Markdown, headings at H1, a body that matched the
composer verbatim — and was still wrong in two reader-visible ways. Type and
structure validation cannot catch "the ordinal appears twice" or "the scaffolding
leaked"; only a witness that asserts the *substance* of the line can.

## The cure that held: normalize at the boundary, and let the seam stay single

Both fixes obey the One Law — normalize where the external (LLM) data enters our
rendering, not downstream where it manifests:

- FR-495 strips the self-asserted prefix *in the composer*, the single seam that
  owns the heading, via one module-level compiled regex. `render.py` inherits the
  fix for free because it reuses the composer verbatim (FR-494 J3). The `\s+`
  after the label is the safety guard the judgment froze a test around: a real
  title that merely *begins* "Children of the Thaw" / "Chapter Endings" is left
  untouched. The fourth special case would be the signal to escalate to a parser
  (J5) — we stopped at the first.
- FR-496 glosses the `SUMMARY:` value alone, case- and whitespace-tolerant, with a
  plain-prose fallback so FR-494's paragraph behaviour survives for unlabeled
  cards. Restricted to `SUMMARY:` — no generic `^[A-Z]+:` stripper, because a
  generic stripper is the speculative extension the judgment forbade.

The judging caught my own diagnostic error before code: FR-496's first draft
claimed "the first paragraph *is* the SUMMARY line." False. The whole sheet leaks
*because* there are no blank lines to split on. The cure was right; the stated
reason was wrong. Naming the real mechanism (single-`\n` sheet) made the fallback
test obviously necessary.

## Heuristic

**The demo is a test boundary.** A green unit suite proves the contract you
imagined; the first live run proves the contract the upstream system actually
emits. Read real output as the end consumer before declaring a render "done" —
the cheapest reader-visible bug is the one you see in your own sample, not the one
a user reports. Then pin it with a witness that asserts the *substance* of the
line, not just its shape.

**Seed:** Could the DM prototype carry a tiny golden-sample test — one real
captured story doc, rendered, with a handful of substance assertions — so that the
next upstream prompt drift (a new label, a new title mannerism) fails a check
instead of a reader?
