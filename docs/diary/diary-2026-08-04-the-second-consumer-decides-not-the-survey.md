# Are More Feeders Needed? The Second Consumer Decides, Not the Survey

**Date:** 2026-08-04
**Context:** Post-FR-773 reflection. The shared document splitter shipped as the first feeder manifest. The session's map-survey found 14 tool-fed map nodes in four families — splitters, corpus listers (×4), fetchers (×3), combinators (×2). The obvious next question: extract the rest?

## The pull

The survey has the shape of a backlog. Four corpus listers
(`list_diary_files`, `list_prompts`, `load_prompts_node`, `load_corpus`)
all do glob → read → list-of-dicts; three fetchers do URL → text; two
combinators do list × list. The graduation rule ("appears twice → FR")
seems to fire three times at once. That pull is exactly
`growth_as_default` wearing a pattern-extraction costume — the survey
*describes* recurrence; it does not *name a consumer*.

## What made split_document worth a manifest

Re-reading the shipped feeder against the families, the manifest earned
its existence on three properties the others mostly lack:

1. **Nontrivial boundary knowledge.** Poppler binaries, subprocess exit
   codes, page-count parsing, an explicit no-fallback failure contract —
   knowledge paid for once, worth sharing. A ten-line glob has no such
   knowledge; sharing it saves nothing and adds an import edge.
2. **A named first consumer at birth.** book-summary existed in the same
   FR. `would_you_use_this` had an answer before the tool did.
3. **Kwargs-shaped already.** The corpus listers are all
   `def f(state: dict) -> dict` python-node functions with domain-pinned
   globs (`docs/diary/*.md`, prompt dirs, corpus paths). Extracting them
   means redesigning to the FR-772 kwargs contract *and* parameterizing
   the domain pin — at which point each caller passes its glob and the
   "shared tool" is a wrapper around `Path.glob` with extra steps.

## Verdict

No more feeders now. Two candidates have a real trigger condition, and
the condition is a **second consumer with the same failure contract**,
not survey recurrence:

- **Fetcher** (`fetch_url → text`): the strongest future candidate — it
  carries genuine boundary knowledge (timeouts, encodings, HTTP failure
  taxonomy, robots/rate concerns) like the splitter carried poppler. If
  a new graph needs article text and would otherwise copy
  `fetch_article_content`, that copy-moment is the FR-moment.
- **Corpus lister**: only if a consumer needs the *contract* (stable
  ordering, missing-dir ValueError, index/text chunk shape) rather than
  the ten lines. The shape convergence with split_document's
  `{"chunks": [{"index", "text"}]}` is suggestive — a common feeder
  output shape would let demos swap feeders — but that is an
  architecture question deserving its own FR, not a silent extraction.
- **Combinators**: no — `cartesian_product` is domain-glue, and the
  general form is a one-line itertools call.

## Heuristic

A survey is inventory, not a backlog (`research_as_inventory`). A feeder
earns a shared manifest when it has (a) boundary knowledge worth paying
for once, and (b) a second consumer who would otherwise copy it. Count
copy-moments, not pattern-matches.

**Seed:** Should feeder tools converge on a canonical output shape —
`{"chunks": [{"index": int, "text": str}], "total": int}` — so any
feeder can drive any map/reduce demo interchangeably? If a second feeder
(the fetcher) ever ships, that FR should decide the shape question
explicitly rather than inherit it by accident.
