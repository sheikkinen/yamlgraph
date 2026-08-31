# The Question Above the Question

**Date:** 2026-08-31
**Arc:** docs/plan-web-toolkit.md revs 9–11 (PRs #534–#539) + FR-936 judgement
(SPLIT) + FR-939 full plan→research→judge cycle. Successor to
diary-2026-08-31-the-plan-rewritten-eight-times.md.

## What happened

Three more plan revisions and the first two judge-graph runs of the arc.
Rev 9 pinned mercury-2 and turned tracing off at scale. Rev 10 ran the
source research live and falsified the plan's own founding assumption —
no public bulk .fi list exists; the Traficom claim had survived nine
revisions unverified. Rev 11 was born from a ten-word operator prompt:
"should the yamlgraph just build semantic layer on top of common crawl."
In parallel, FR-936 was judged (SPLIT into four contracts) and its first
split, FR-939 (map overflow policy), went through the full research →
plan → judge cycle to APPROVED WITH REVISIONS.

## Traps encountered

- **The canon fires per-plan, but layers need it per-plane**: rev 8 asked
  `does_the_platform_already_do_this` about LangGraph and shrank D. Nobody
  re-asked it about the *data* layer. All facts for rev 11 were already in
  my own rev 10 research — CC host graph as seed, index-driven WARC
  byte-range fetch — yet I filed Common Crawl under "source" and kept
  planning our own fetch pipeline, politeness engine, and refresh cadence.
  The operator's reframe deleted all three in one sentence: CC is the data
  plane; yamlgraph contributes only the semantic plane. I answered the
  question I was asked (where are the sources) and missed the question
  above it (what should we not build). A platform question answered once
  is not answered for every architectural plane the plan touches.
- **judge_as_junior_pr, vindicated twice by code-reading**: both judge
  runs earned their verdicts from the *code*, not the FR narrative. The
  FR-936 judge found deterministic starvation in the proposed bounded
  shared pool (hung callables never release slots) and that RetryPolicy
  cannot observe map-branch failures because wrap_for_reducer converts
  every exception into a successful state update. The FR-939 judge found
  that `config.max_map_items` is parsed at load and then never propagated
  to `map_edge` — dead config the author's own precedence table asserted
  was live. Input closure is not a ritual of independence; it is what
  forces the judge to open the file instead of trusting the prose.
- **prior-art-at-birth, still not a habit**: the prior-art gate fired
  three times this session (two judgements, one research record), each
  cured post-hoc with a disposition line. The gate works; the authoring
  habit lags it. Any new file under feature-requests/ needs its
  **Prior art:** line written at creation, not at commit failure.
- **falsified assumption as the cheapest research output**: rev 10's most
  valuable finding was negative — the bulk-list assumption was wrong. One
  live check killed a nine-revision-old premise the plan's sequencing
  depended on. Assumptions inherited across revisions accrue false
  authority from survival alone; survival is not verification.

## Heuristic

Ask `does_the_platform_already_do_this` once per architectural plane —
framework, data, infra — not once per plan. A plan that names an external
corpus, registry, or index as a "source" should immediately be re-read
with that source promoted to "platform": what does it already crawl,
dedupe, version, and refresh that the plan proposes to rebuild? The rev
11 delta (81 insertions that mostly deleted obligations) was available at
rev 10 for the cost of one re-read.

Second heuristic: the judge graph's highest-value outputs this session
were wiring defects (dead config, exception-swallowing reducer) invisible
in any FR text. Point the judge at code paths the FR *claims*, not just
the FR's internal consistency — the FR-939 judgement did this unprompted
and it should be the expectation, not a bonus.

**Seed:** The per-plane platform question is mechanizable: a plan-review
gate that extracts every named external system from the plan and asks,
for each, "source or platform?" — one LLM call per noun, map node,
five-minute run. Would it have caught Common Crawl at rev 3, when C was
first promoted?
