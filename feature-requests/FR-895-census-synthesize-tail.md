# Feature Request: Census Synthesize Tail — The Stage the Human Reads

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-27); R-1..R-6 folded below; see [FR-895-census-synthesize-tail.judgement.md](FR-895-census-synthesize-tail.judgement.md)
**Effort:** 0.5 day
**Requested:** 2026-08-27
**First consumer / first event:** the diary census re-run — after
aggregation, one synthesis call writes `docs/diary/census/brief-<date>.md`
answering "what does this corpus say?" with row citations; the operator's
2026-08-27 question ("is there a human readable summary?") gets a
regenerable yes. Second consumer: the PDF/git proof configurations.
**Research:** [FR-895.research.md](FR-895.research.md)

**Prior art:** **[reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md)
(FR-894) is the canonical pattern guide this FR extends** — its six-stage
topology ends at "render"; this FR adds the cited-narrative synthesis the
guide's own reduce rule constrains ("no reduction may erase the primary
per-item findings") and must satisfy its eight invariants, including the
hidden-canary invariant (#8) this lane contributed. FR-892 (census
pipeline — its Proposed Solution carried this stage as "optional tail
synthesis node"; the authoring brief deleted it as scope creep — this FR
is the restoration, optional-no-more; diary
2026-08-27-optional-is-where-value-goes-to-die.md is the loss post-mortem).
FR-893 (diary census — its headline finding was hand-written prose,
irreproducible on re-run; the motivating consumer). fr_atlas demo
(deterministic collection → one story judgement → dated committed
artifact — the in-repo shape precedent named by the research run).
Mercury study run-1 C5S1 ("executive brief" ⭐5 cell — the pattern's own
naming of this stage).

## Summary

Add the pattern's fifth stage as a first-class, non-optional output: a
**single pinned-LLM synthesis call** over the aggregated/reduced artifact
(never the raw fan-out) producing a cited human-readable brief — markdown
narrative where every claim carries ledger-row/label citations — plus an
**LLM-free citation boundary** that validates every cited row exists in
the source artifact before the brief is accepted (narrative claims are
CLAIMS; the boundary reconciles them — `two_strike_split` lineage,
supported by the librarian's external precedent on provenance-constrained
narrative generation). Wired as: an optional-input, mandatory-output tail
for `corpus_census` runs and a `--brief` mode in the diary census flow.

## Value Statement

Every census run ends with the question it was commissioned for answered
— "what does this corpus say?" — regenerably, with citations, instead of
a hand-written FR note or nothing.

## Problem

See the closed brief
([census-human-readable-tail.md](research-briefs/census-human-readable-tail.md)):
no shipped pipeline stage has the human as its reader; the value was lost
through the optional→deleted lineage; the diary census's headline finding
is not reproducible by re-running.

## Ideal Result

A maintainer re-runs any census and reads one committed brief: 3–10
paragraphs, top findings ranked, every claim citing rows/labels that the
boundary has verified exist, honest about abstention rates and coverage.
The 3-row proof ledger yields three sentences; the 1700-label diary
aggregation yields the alias-consolidation headline no one has to
rediscover by hand.

## Proposed Solution

Per the research table (canary recalled by 2 personas; dissents folded):

1. **Synthesis stage** — one LLM call (pinned model; synthesis tier may
   exceed map tier per cheap-map discipline: single call over an
   aggregated artifact), consuming the recurrence table / ledger and
   emitting **structured claim blocks (R-1): each claim carries
   `claim_id`, `text`, `citations` ([label] / [row:item_ref]), optional
   `confidence`** — never free markdown. Graph change (adding the tail
   node to corpus_census) goes through the sole authoring route; this FR
   may modify ONLY `examples/demos/corpus_census/graph.yaml` and its
   prompt files, plus code-side citation/brief helpers and wrappers (R-6).
   **Bounded input (R-4): a deterministic rows/chars ceiling with a
   top-N-by-count selection rule compacts the aggregate before the call;
   provider, model, prompt version, source-artifact hash, run id, call
   count, timeout, and output path are recorded in brief metadata.**
2. **Citation boundary (LLM-free, R-1 mechanical rule)** — validates:
   every cited label/row exists in the source artifact; every claim block
   has ≥1 citation; no citation points outside the source. Markdown is
   RENDERED only after validation passes — the boundary checks structure,
   never interprets prose.
   **Fail-closed contract (R-2, frozen): on validation failure NO
   `brief-<date>.md` is emitted; the deterministic summary head (top-N
   table, code-generated) is written to a separate
   `brief-<date>.REJECTED.md` failure artifact with the rejection
   reasons.** The accepted brief = deterministic summary head + validated
   rendered narrative.
3. **Public-safe inheritance (R-5, mechanical)** — the synthesis input is
   the aggregated public-safe artifact ONLY; the brief renderer has no
   access to raw evidence-span text for committed outputs; tests assert
   the input fixture contains only allowed columns. os-infra dissent
   (pure LLM-free filter) recorded as fallback.
4. **Wiring (R-3, exact invocation)** — the census graph tail requires
   new variables `brief_path` and `brief_rubric` (with the synthesis
   prompt as a graph prompt artifact); missing brief inputs fail loudly
   before synthesis. `scripts/diary_census.sh` gains the brief step
   passing them; the PDF-library and git-timeline proof commands are
   updated to pass them (C-6: silent omission of the human output is not
   allowed for named consumers).

## Acceptance Criteria (revised per judgement — supersede the original set)

- [ ] AC-01: RED first — failing citation-boundary tests: fabricated row citation, fabricated label citation, claim without citation, citation outside source — each rejected; no accepted narrative artifact emitted on failure (R-2 contract).
- [ ] AC-02: Brief output is structured claim blocks; markdown rendered only after the boundary accepts them.
- [ ] AC-03: Synthesize tail authored via scripts/author.sh with lint+smoke in the authoring report; exactly one pinned synthesis call over the reduced artifact, never over raw corpus items.
- [ ] AC-04: Invocation semantics documented and tested: brief_path/brief_rubric named; missing inputs fail loudly before synthesis; PDF, git-timeline, and diary commands all pass them.
- [ ] AC-05: Synthesis input bounded by a deterministic ceiling + selection rule; provider/model/prompt version/source hash/run id/call count/timeout/output path recorded in proof metadata.
- [ ] AC-06: Regenerated PDF-library and git-timeline briefs committed alongside ledgers; the 3-row corpus yields a proportionate brief, zero dangling citations.
- [ ] AC-07: Diary brief docs/diary/census/brief-<date>.md: top finding mechanically checked against the known alias-of-doctrine headline via cited label families, not prose match.
- [ ] AC-08: Public-safe tests: briefs generated only from aggregated fields; no raw evidence-span text.
- [ ] AC-09: Summary-head/fallback behavior tested for both accepted and rejected narrative cases.
- [ ] AC-10: Changelog fragment, REQ tagging, FR status update, diary reflection.

## Out of Scope

- Summaries for non-census graphs (generalize only after a second
  consumer class exists).
- Any LLM in the validation path (boundary is code).
- Regenerating historical briefs for past runs.
- The LedgerMind external framework (librarian precedent, not a
  dependency).

## Alternatives Considered

See [FR-895.research.md](FR-895.research.md): LLM-free ledger-to-narrative
filter (os-infra — folded as fallback + summary head); deterministic
summary section only (subtractionist — folded as the boundary's
degraded-mode output; alone it cannot answer "what does this corpus say"
across 1700 labels); LedgerMind three-layer grounding (librarian,
arXiv-cited — precedent for the citation boundary, not adopted as
dependency); status quo hand-written prose (the witnessed defect).

## Related

- **reference/patterns/corpus-map-reduce.md (FR-894)** — the canonical
  guide; this FR's brief must satisfy its eight invariants, and the
  citation boundary implements its render-stage evidence contract
- FR-892/FR-893 (the pipeline and its first consumer), fr_atlas (shape
  precedent), diary 2026-08-27-optional-is-where-value-goes-to-die.md
- Scripture: `who_reads_this_when` (per-stage application), cheap-map
  tail discipline, `plausible_wrong_answer` (the boundary's reason)
