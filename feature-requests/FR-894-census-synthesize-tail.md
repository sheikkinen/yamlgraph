# Feature Request: Census Synthesize Tail — The Stage the Human Reads

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-27
**First consumer / first event:** the diary census re-run — after
aggregation, one synthesis call writes `docs/diary/census/brief-<date>.md`
answering "what does this corpus say?" with row citations; the operator's
2026-08-27 question ("is there a human readable summary?") gets a
regenerable yes. Second consumer: the PDF/git proof configurations.
**Research:** [FR-894.research.md](FR-894.research.md)

**Prior art:** FR-892 (census pipeline — its Proposed Solution carried
this stage as "optional tail synthesis node"; the authoring brief deleted
it as scope creep — this FR is the restoration, optional-no-more; diary
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
   emitting a markdown brief with `[label]`/`[row:item_ref]` citations.
   Graph change (adding the tail node to corpus_census) goes through the
   sole authoring route (C-3 lineage).
2. **Citation boundary (LLM-free)** — validates every citation resolves
   to a real row/label in the source artifact; uncited claims and
   dangling citations fail the brief (fail closed, no partial narrative).
   Subtractionist dissent folded: the boundary ALSO prepends a
   deterministic summary head (top-N table) so the brief degrades to
   useful even if the narrative is rejected.
3. **Public-safe inheritance** — the brief consumes only the aggregated
   public-safe artifacts (never raw evidence spans) for committed
   outputs; os-infra dissent (pure filter, no LLM) recorded as the
   fallback if narrative fidelity proves untrustworthy at scale.
4. **Wiring** — diary census wrapper gains the brief step; proof
   configurations regenerate briefs as demo evidence.

## Acceptance Criteria

- [ ] AC-01: RED first — failing tests for the citation boundary: dangling citation rejected, uncited-claim policy enforced, deterministic summary head present, brief rejected without partial output.
- [ ] AC-02: The synthesis tail is added to corpus_census via the sole authoring route with lint+smoke evidence; single call, pinned model, never fan-out.
- [ ] AC-03: Proof regeneration: PDF-library and git-timeline briefs committed alongside their ledgers; 3-row corpus yields a proportionate brief.
- [ ] AC-04: Diary census brief: re-run aggregation + tail produces docs/diary/census/brief-<date>.md whose top finding matches the known headline (alias-of-doctrine recurrences) with verified citations — the canary for this FR.
- [ ] AC-05: Citation boundary witnessed: a fixture brief with a fabricated citation fails closed; committed briefs contain zero unverifiable citations.
- [ ] AC-06: Public-safe: committed briefs contain no raw evidence spans; witnessed by test.
- [ ] AC-07: Changelog fragment, REQ tagging, FR status update, diary reflection.

## Out of Scope

- Summaries for non-census graphs (generalize only after a second
  consumer class exists).
- Any LLM in the validation path (boundary is code).
- Regenerating historical briefs for past runs.
- The LedgerMind external framework (librarian precedent, not a
  dependency).

## Alternatives Considered

See [FR-894.research.md](FR-894.research.md): LLM-free ledger-to-narrative
filter (os-infra — folded as fallback + summary head); deterministic
summary section only (subtractionist — folded as the boundary's
degraded-mode output; alone it cannot answer "what does this corpus say"
across 1700 labels); LedgerMind three-layer grounding (librarian,
arXiv-cited — precedent for the citation boundary, not adopted as
dependency); status quo hand-written prose (the witnessed defect).

## Related

- FR-892/FR-893 (the pipeline and its first consumer), fr_atlas (shape
  precedent), diary 2026-08-27-optional-is-where-value-goes-to-die.md
- Scripture: `who_reads_this_when` (per-stage application), cheap-map
  tail discipline, `plausible_wrong_answer` (the boundary's reason)
