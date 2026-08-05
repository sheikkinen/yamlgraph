# 2026-08-05 — The First Real Book Is the Cheapest Inquisitor

FR-773 shipped a book-summary demo that was green everywhere it was measured:
23 unit tests, a lint pass, a fixture smoke with a clean summary. One day later
the operator ran it on an actual 418-page book and it produced three defects in
a single run — silent truncation to 100 pages, LLM commentary about blank
pages, and a discovered absence (no OCR/vision path) that the docs had never
admitted. FR-774 exists entirely because of that one run.

**The trap:** the fixture was designed by the same mind that designed the
splitter, so it inhabited exactly the envelope the splitter already handled —
2 pages, dense text, no scans. Test fixtures are a projection of the author's
imagination; a real artifact is a projection of the world. The world is wider.
This is `plausible_wrong_answer` at the corpus level: the demo passed every
shape check while being semantically unfit for its stated purpose
("summarize a book" — books are 400 pages, not 2).

**The recurrence worth naming:** the judge's R-4 caught a success-shaped empty
chunk list — the *same* silent-fallback class the FR-773 judge had already
flagged once (`min_chars` filtering everything and returning `[]` with
`success: True`). Two consecutive FRs, same author, same defect family.
Commandment 6's "when a filter yields nothing, raise" is evidently not yet
internalized as a reflex at authoring time; it still requires the judge. That
asymmetry — author writes the filter, judge writes the raise — is the
plan-judge separation earning its cost twice in two days.

**A small mechanization win:** the committed RED test demanded README language
("1000", no "page-by-page") that the sole-route authoring agent then had to
satisfy — so the route self-extended to repair the docs without being asked.
A test that asserts on prose turns documentation drift into a red bar.
Test-driven doc repair works.

**Validation record:** 23/23 tests; fixture smoke clean; and the original
failing artifact itself — tmp/book1.pdf, 418 pages — rerun end-to-end: 42
excerpt branches executed, zero truncation warnings, coherent whole-book
summary. Closing the loop on the *reported* input, not a proxy for it, is the
only closure that answers the report.

**Seed:** Could the demo-gate require one *external* artifact run — an input
not authored in this repo — before a demo claims its noun ("book", "codebase",
"conversation")? The fixture proves the pipeline wiring; only a foreign
artifact proves the noun. What would a cheap "bring your own corpus" witness
look like as a gate?
