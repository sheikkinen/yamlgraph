# Feature Request: FR-500 — `book_editor` review-driven editing loop (stand-alone example)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — MVP frozen, converging loop deferred (2026-06-16); see Judgement
**Effort:** 2–3 days
**Requested:** 2026-06-16

## Summary

A new stand-alone YAMLGraph example, `examples/book_editor/`, that consumes the
**structured, located findings** emitted by `book_reviewer` (FR-497) and applies a
**span-scoped editing pass** to a book-shaped Markdown manuscript, then **re-reviews
only the touched seams** and loops until continuity converges (or a cap, then
raises). It closes the loop `generate → review → edit → re-review`, turning the
reviewer from a terminal report into a feedback system — and is the only one of the
three continuity fixes that can **repair a manuscript already written** (e.g. the
*Floodmark Saga*), independent of how it was generated.

## Value Statement

A finished book with located defects can be **mechanically repaired**: because each
`book_reviewer` continuity break already cites both chapters and the exact
contradicting sentences, the editor rewrites only those cited spans — a precise work
order, not "make it more consistent" — and a bounded re-review loop proves the edit
actually closed the break instead of spawning a new one, yielding a measurably higher
continuity score on the same manuscript.

## Problem

FR-498 (roster faction/inventory) and FR-499 (typed ledger + enforced gate) fix
continuity *at generation time* — but they only help books generated **after** they
land. The *Floodmark Saga* and any hand-written or already-produced manuscript still
carry their breaks. The `book_reviewer` (FR-497) **diagnoses** those breaks with
quotable precision but **changes nothing**: its `review.md` is a dead end. There is
no artifact that *acts* on the findings.

There is also a doctrinal hazard to respect (Scripture: `downstream_fix`): naive
whole-chapter rewriting treats symptoms and a local patch can introduce a new break
(fix Ch2's clan → now Ch3 disagrees). The editor must therefore be **span-scoped**
and **loop-verified**, not a free rewrite.

## Proposed Solution

A first-class example (sibling of `examples/book_reviewer` and
`examples/book_translator`) — its **own** graph, NOT a DM component, NOT importing DM
code, reading only a book-shaped `.md`:

```
manuscript.md ─▶ review (reuse book_reviewer pipeline) ─▶ findings (located breaks)
                                                              │
        ┌─────────────────────────────────────────────────────┘
        ▼
  edit (map over findings):  per break, rewrite ONLY the cited span(s)
        ▼
  re-review TOUCHED PAIRS only ─▶ converged?  ── no ──▶ loop (capped)
        │ yes / cap reached
        ▼
  write edited manuscript + edit-report.md  (raise if cap hit unconverged — J5 honesty)
```

Key constraints (each maps to a doctrine guardrail):

- **Span-scoped edits.** The editor rewrites only the sentences a finding cites,
  preserving everything else — fixes at the callsite, not the whole chapter
  (`callsite_fix`).
- **Bounded converging loop.** Re-review only the pairs whose spans changed; loop
  until continuity is clean or an iteration cap is hit, then **raise** rather than
  emit a still-broken book claimed as fixed (`partial_remediation`, J5).
- **No new break introduced.** The loop's re-review is the proof the edit didn't
  trade one contradiction for another.
- **Computed, not asked.** Reuse `book_reviewer`'s decomposed reduce for the
  convergence check — the LLM edits prose; Python decides "converged" (K3/K4).

As a stand-alone **example** (not the DM prototype), FR-474 J3 does **not** apply
(per FR-497 J1): it is first-class, gets **no** CAP file and **no** `@pytest.mark.req`
markers as an *example*, is committed with an honest `feat(book-editor): FR-500 …`
type, and requires a changelog fragment + diary. Pure unit tests (mock-LLM graph
run, span-scope asserts, convergence/cap behavior) plus one captured live e2e run on
the *Floodmark* `story.md`.

## Acceptance Criteria

- [ ] `examples/book_editor/graph.yaml` lints clean; reuses the `book_reviewer`
      review/reduce pipeline for diagnosis and convergence (no whole-book LLM judge).
- [ ] Editor rewrites only cited spans; an asserting test proves untouched
      paragraphs are byte-identical.
- [ ] Bounded loop: converges on a clean continuity pass, or raises at the cap with
      the remaining breaks named (no silent partial fix).
- [ ] Live e2e on `outputs/dungeon-master/10000-BC/story.md` produces an edited
      manuscript whose `book_reviewer` continuity score beats the FR-497 baseline
      (1/5); captured to a log.
- [ ] Example listed in `examples/README.md`; README, changelog fragment, diary
      added. No CAP, no req markers, no `FR-474 J3` trailer.

## Alternatives Considered

- **Fold editing into `book_reviewer`.** Conflates diagnosis with mutation and
  breaks the example's text-in/typed-evaluation-out contract. Keep them separate;
  the editor *consumes* the reviewer.
- **Whole-chapter regeneration from findings.** Cheaper to write, but discards good
  prose and is a `downstream_fix` magnet (high risk of new breaks). Rejected in
  favor of span-scoped edits.
- **Only fix generation (FR-498/499), skip the editor.** Leaves every existing
  manuscript unrepairable; the editor is the sole retrofit path and closes the
  feedback loop.

## Related

- FR-497 — `book_reviewer` (the upstream diagnosis this example consumes)
- FR-498, FR-499 — generation-time continuity fixes (complementary; this is the
  retrofit/feedback half)
- `examples/book_reviewer/`, `examples/book_translator/` (sibling-example layout)
- `outputs/dungeon-master/10000-BC/review.md` (the located findings to act on)

## Judgement — 2026-06-16 (scope frozen with amendments)

**Status:** Judged — scope frozen. The architecture is sound but two premises were
softened to match what the reviewer actually emits.

**Red Hat — is the pain real?** Two distinct values, both real: (1) it is the **only**
retrofit path for books already written (Floodmark cannot benefit from FR-498/499);
(2) it closes the reviewer's feedback loop. Authorized — but see J4 on de-risking.

- **J1 (reviewer reuse — confirm the contract, don't assume a subgraph).** Reusing
  `book_reviewer` is correct (CAP-111 shared-graph invocation / `shared:` exists),
  but the editor needs the reviewer's **typed findings**, which today are produced
  *inside* its reduce and rendered to `review.md`. Ruling: the editor consumes the
  reviewer's **`review` state dict** (the structured `BookReview`), NOT the markdown.
  If invoking the whole graph as a subgraph is friction, calling the reviewer's pure
  parse+map+reduce path directly is acceptable — the constraint is *typed findings
  in, no second almighty judge*, not a specific invocation mechanism.
- **J2 (span location is a TOLERANT-MATCH boundary — the key risk).** The
  Proposed plan says "rewrite only the cited span". But `book_reviewer` findings
  cite **quoted sentences in prose**, not line offsets — and an LLM-quoted sentence
  may not be a byte-exact substring of the manuscript (smart quotes, ellipsis,
  whitespace, paraphrase). Ruling: locating the span is a `tolerant_matching`
  problem (normalize → contains/fuzzy), and the acceptance test MUST cover a
  near-miss quote, not just an exact hit. This is the single most likely failure
  point; name it now.
- **J3 (the byte-identical assertion needs a defined granularity).** "Untouched
  paragraphs are byte-identical" is the right guard, but only holds at **paragraph**
  granularity (the editor rewrites a paragraph containing the cited span, not the
  whole chapter). Freeze the unit of edit = the **paragraph** containing a cited
  span; assert all *other* paragraphs are byte-identical.
- **J4 (de-risk: editor BEFORE the converging loop).** The span-scoped editor and
  the bounded re-review loop are separable. The editor (locate span → rewrite
  paragraph → re-review touched pairs **once**, report) delivers the retrofit value
  and proves J2/J3. The **iterative** loop-to-convergence adds control-flow risk
  (oscillation, cap tuning). Ruling: **single-pass edit + one re-review is the
  frozen MVP**; the multi-iteration converging loop is a documented follow-on, not
  required for first landing. (Mirrors FR-499's split rationale.)
- **J5 (raise honestly).** If the single re-review still shows the targeted break
  unresolved, the run **reports it unresolved** (does not claim success) — the J5
  "no half-fix masquerading as done" stance. With the loop deferred (J4), "raise at
  cap" becomes "report unresolved breaks after one pass".
- **J6 (regime — first-class example, NOT prototype).** Per FR-497 J1, `book_editor`
  is a first-class example: **no** CAP, **no** `@pytest.mark.req` markers (as an
  example), honest `feat(book-editor): FR-500 …`, **no** `FR-474 J3` trailer,
  changelog fragment + diary + `examples/README.md` entry required.
- **J7 (regression oracle).** Success = the edited Floodmark `story.md`, re-reviewed
  by `book_reviewer`, beats the 1/5 continuity baseline on the targeted breaks
  (witness log).

**Frozen — MVP acceptance** (converging loop deferred per J4):
1. `examples/book_editor/graph.yaml` lints clean; consumes the reviewer's typed
   `review` dict (no second whole-book LLM judge).
2. Span location uses tolerant matching; a test covers a **near-miss** quote.
3. Edit granularity = the paragraph containing a cited span; all other paragraphs
   asserted byte-identical.
4. Single-pass: edit cited paragraphs → re-review touched pairs once → report;
   unresolved breaks reported honestly (no false success).
5. Live e2e on Floodmark `story.md` beats the 1/5 continuity baseline on the
   targeted breaks (witness log).
6. `examples/README.md` entry; README + changelog fragment + diary. No CAP, no req
   markers, no J3 trailer.

**Follow-on (Proposed):** the iterative re-review-to-convergence loop with an
iteration cap.

---

## Sequencing ruling (FR-498 / 499 / 500)

All three judged and frozen. Execution order by boundary, cheapest-first; each is
independently shippable:

1. **FR-498** (front boundary, ~0.5–1d) — supplies the canonical `FACTION:` token.
2. **FR-499 Phase A** (between-chapter, typed ledger) — consumes FR-498's token.
   Phase B (enforcement) gated on Phase A's witness.
3. **FR-500 MVP** (retrofit/feedback) — independent of 498/499; the only fix for
   already-written books. Can proceed in parallel with 498/499.

The `book_reviewer` continuity score on a regenerated (498/499) or edited (500)
Floodmark book is the shared regression oracle for all three.
