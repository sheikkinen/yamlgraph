# Feature Request: Prior-art retrieval inside the research route

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved with revisions (folded 2026-08-30)
**Effort:** 1 day
**Requested:** 2026-08-30
**First consumer / first event:** the Judge, at the next
`scripts/judge.sh` run on an FR created after this lands — it opens
`feature-requests/FR-NNN.research.md` and reads a retrieved,
status-annotated prior-art block at the head of the table instead of
inferring precedent from persona prose.
**Research:** [FR-932.research.md](FR-932.research.md)
**Judgement:** [FR-932-prior-art-retrieval-in-research-route.judgement.md](FR-932-prior-art-retrieval-in-research-route.judgement.md)
— APPROVED WITH REVISIONS; R-1 through R-3 of the judgement are folded
below, and the measurement the judgement relied on was corrected
downward by the author before enforcement (see Measurement).
**Prior art:** FR-737 (prior-art hook) and FR-738 (pre-commit
disposition gate) are the direct territory: both are Completed and both
retrieve *after* the FR file exists. This FR does not replace either —
it adds a third caller of the same retrieval function at an earlier
point, changes that function by exactly one defaulted keyword (R-1),
and pins the gate untouched (R-7). FR-890 and FR-896
(research sole route, artifact schema) are the other direct territory;
this FR extends the deterministic context block those FRs introduced,
under the same author-independence constraint. FR-814 (FR knowledge
graph augmentation) is inherited transitively through `build_prior_art`
and not re-litigated. Filename-noun hits on "prior/art/research" in
`feature-requests/research-briefs/` are distinguished in the problem
brief.

## Summary

The research route runs blind to the feature-request corpus, yet its
frozen artifact schema requires a `precedent` citation from every
persona. Retrieve the corpus once, deterministically, before the
personas run; ground them on the result; and write that retrieval into
the research report so the Judge reads a lookup rather than an
assertion.

## Value Statement

The Judge's two evidence requirements — dispositioned prior art and a
substantive research record — stop being two disconnected artifacts
produced by two mechanisms at two times, and become one committed
record whose precedent claims can be looked up.

## Problem

`.github/skills/judge-fr/doctrine.md` withholds authority on two
grounds: undispositioned prior art (FR-737 precedent rule, REJECTED FRs
included) and absent or strawman research (FR-890 clause). Those two
grounds are served by two mechanisms that never meet.

Prior-art retrieval (`.github/hooks/scripts/checks/prior_art.py`) fires
on FR *file creation* — after research has already generated, ranked
and reduced the alternatives. Its output is advisory stdout;
`prior_art_gate.py` then fails a commit that lacks a `**Prior art:**`
marker, checking the marker's presence and nothing about its content.

The research route (`scripts/research.sh` →
`examples/demos/research-route/graph.yaml`) grounds its five personas on
exactly one deterministic block, `collect_committed_context`: CAP
one-liners, `ARCHITECTURE.md` headings, Scripture trap/cure keys. No
node reads `feature-requests/`. The personas are required by
`scripts/research_preflight.py` to fill a non-empty `precedent` cell
from a context window containing no precedent corpus.

Measured over the twelve committed research artifacts (60 rows) using
the repo's own validator, `_classify_precedent`, rather than a naive
regex: 37 cells cite an `FR-`/`NC-`/`CAP-` identifier, 13 are librarian
URLs, 1 cites other committed state, and 14 are untraceable. **All 14
untraceable rows sit in five artifacts (FR-888, 893, 895, 896, 897)
that predate the FR-896 reducer**, which now raises on exactly that
case. The "cells cite nothing" hole is already closed; this FR does not
re-open it.

The defect that survives that correction is sharper. Of the 35 repo
identifiers cited across all thirteen research runs ever executed, **20
were already written in the brief by the author** and 11 more are `CAP-`
identifiers supplied by `collect_committed_context`. That leaves **four
novel FR identifiers in the entire history of the route** — FR-164,
FR-254 and FR-892 (twice). The validator confirms a cited FR exists;
nothing confirms it was *found*. In thirteen runs the research route has
never retrieved a feature request, because it has never read the
directory they live in. Precedent is being recited from the author's own
brief and from model memory, and passing a check that only asks whether
the identifier resolves.

The step that most needs the record of what was already tried is the
step run without it; the step that retrieves the record runs after the
conclusions are frozen.

## Ideal Result

A precedent claim in the record before the Judge is a retrieval result,
not an assertion. One deterministic retrieval over the feature-request
corpus runs before any persona reasons; its ranked, status-annotated
hits ground every persona; and the same hits are printed verbatim into
the research report, so the Judge can see both what was found and what
each persona did with it. When the retrieval finds nothing, the report
says so explicitly, distinguishing "no prior art" from "no retrieval".

## Measurement before design

Two measurements were run before the design was frozen, and both
changed it (`read_raw_output_first`).

**A. The reuse mechanism does not work.** The first draft proposed
reusing `build_prior_art` verbatim. Querying the 854-file
`feature-requests/` corpus with each committed research-brief filename:

| query filenames | hits returned | silent |
|---|---|---|
| 14 research briefs | 3 | **11** |
| 9 recent FR filenames (FR-920…929) | 5 | **4** |

This FR's own brief filename (`prior, art, precedent, brief`) returns
**nothing** against the FR corpus, while returning five hits against the
13-file `research-briefs/` directory.

The cause is `RARE_MAX_FILES = 20`, an absolute floor: a noun counts as
rare only if it appears in ≤ 20 files. At 854 files that is 2.3%, so any
noun with ordinary currency in this repo is disqualified and
`build_prior_art` returns `""`. FR-737 F2+A1 predicted this in its own
comment — "absolute; ≈3% today, tightens as the corpus grows". This is
the witnessed miss `two_strike_split` and FR-737 F4 required.

The distinction the numbers force: **the rarity floor is a notification
policy, not a retrieval policy.** It exists so an advisory hook that
interrupts an author stays silent rather than crying wolf. A grounding
block inside a research run interrupts nobody — an irrelevant line in a
context window costs far less than a missing precedent. The two
consumers need the same ranking and different floors.

**B. The original defect claim was overstated, and the corrected one is
worse.** The first draft claimed "15 of 60 precedent cells cite
nothing", derived from an author-written regex. Re-running the count
through the repo's own `_classify_precedent` showed 14 untraceable rows,
all of them in artifacts predating the FR-896 reducer that now raises on
that case — a closed hole, not an open one. The corrected measurement in
the Problem section (4 novel FR identifiers across 13 runs) is the claim
this FR stands on. Recording the correction here rather than silently
swapping the number: the judgement was rendered against the weaker
claim, and the enforcer should know which number is load-bearing.

## Proposed Solution

Four changes, all inside the existing research route. No new mechanism,
no new artifact, no schema column.

**1. Retrieve, with the notification floor lifted for this consumer.**
`build_prior_art` gains one keyword argument, `rare_floor: bool = True`.
The default preserves both existing callers byte-for-byte; the research
route passes `rare_floor=False`, keeping noun extraction, status
annotation, `_weighted_zone` weighting, IDF ranking, FR-814 cluster
boost, self-exclusion and the `TOP_N` = 5 bound, and dropping only the
`rare` gate that returns `""`.

`examples/demos/research-route/nodes/research_tools.py` loads the
module by file path — the same `importlib.util.spec_from_file_location`
technique `prior_art_gate.py` already uses as its second caller.

The query path is synthetic: `Path("feature-requests") /
"<brief-stem>.md"`. `build_prior_art` derives nouns from the query
file's *name* and scopes the corpus to the query file's *parent
directory*. Querying with the brief's real path searches the 13-file
`research-briefs/` directory; the synthetic `feature-requests/` path
searches the 854-file FR corpus with the same nouns. The file need not
exist — it is used only for noun extraction, self-exclusion and the
FR-ID regex.

**2. Ground the personas.** The hit block becomes a new sub-section of
`collect_committed_context`, alongside the CAP one-liners:

```
### Prior art retrieved for this brief (filename-noun, IDF-ranked)
FR-737-graveyard-hook-prior-art-on-fr-creation.md  [Completed]  matches: art
FR-070-gui-web-playground.md                       [REJECTED]   matches: playground
```

At most `TOP_N` = 5 hits plus a heading — bounded well under the
existing `_MAX_CONTEXT_LINES` = 300 guard, which keeps raising on
overflow.

**3. Print it into the report.** `write_alternatives` emits the same
block verbatim in the artifact header, under the existing
brief / run-date / personas lines. The Judge then reads the retrieval
and the reasoning in one file. The frozen column set is untouched.

**4. Make the precedent column checkable.** With a corpus now in
context, non-librarian `precedent` cells must carry a committed
identifier, a URL, or the literal token `none-retrieved`. Prose-only
precedent fails. `brief-echo` — the FR-896 demotion that let a row
restate the brief as its own precedent — is rejected in newly generated
artifacts and replaced by `none-retrieved`, which is admitted only when
the retrieval genuinely returned nothing. The token is what a persona
writes when it has no precedent: an honest miss must stay cheaper than
a fabricated citation, and cheaper than an echo.

## Requirements (frozen on judgement)

- **R-1** `build_prior_art` gains exactly one keyword argument,
  `rare_floor: bool = True`. The function has **two** rare gates, not
  one — the `if not rare: return ""` early return and the later
  candidate filter `if any(n in rare for n in matched)` — and
  `rare_floor=False` must lift both. With the floor lifted, the
  eligible noun set is every noun whose corpus frequency is greater
  than zero; the empty return fires only when no query noun matches any
  corpus file. Scoring, `_weighted_zone` weighting, status tags,
  FR-814 cluster boost, self-exclusion and `TOP_N` = 5 are unchanged in
  both modes. (Judgement R-1: the original wording named only the early
  return and would have permitted a no-op.)
- **R-1a** Noun extraction is NOT extended. FR-737 F4 purged
  title/body extraction; the miss measured here is floor calibration,
  not extraction. The module is not relocated.
- **R-1b** Both existing callers (`fr-checks.sh` advisory,
  `prior_art_gate.py` pre-commit) keep the default and are witnessed
  unchanged by their current tests. The floor is lifted only for the
  research consumer.
- **R-2** The query path is `feature-requests/<brief-stem>.md`,
  synthetic, because `build_prior_art` scopes the corpus to the query
  file's parent directory.
- **R-3** Hits enter the run only through `collect_committed_context`,
  preserving FR-890 R-2 author-independence: deterministic, computed
  from committed filenames and `**Status:**` fields, never from the
  author's narrative.
- **R-4** Empty retrieval is reported, not omitted. When the retrieval
  returns `""` — with both floors lifted this means no noun matched any
  file at all — the context block and the artifact header both carry
  exactly `none-retrieved`.
- **R-5** The prior-art block reaches the artifact through state, not
  through recomputation. `graph.yaml` passes
  `brief_path: "{state.brief_path}"` to `collect_committed_context`,
  which computes the subsection once; `write_alternatives` copies that
  subsection out of `state["committed_context"]` into the artifact
  header byte-for-byte and never re-runs retrieval during reduction.
  (Judgement R-3: "the same block verbatim" needs a frozen state edge.)
  No new column; the frozen column set stands.
- **R-6** Precedent row validation is restated in both
  `research_tools.py` and `scripts/research_preflight.py`: a
  non-librarian cell passes with a committed identifier, a URL, or
  `none-retrieved`; `brief-echo` is rejected in newly generated
  artifacts; `none-retrieved` is accepted only when the artifact
  header's prior-art block is exactly `none-retrieved`; and a
  `none-retrieved` row counts toward the existing `non_echo >= 3`
  grounding threshold as grounded-empty, never as an echo. (Judgement
  R-2: without this, an honest no-hit run fails the FR-896 threshold or
  the hollow echo path survives.) Librarian URL and error-string checks
  are unchanged.
- **R-6a** The tightened validation is prospective. The twelve
  committed research artifacts — the measurement baseline — are not
  retro-gated or rewritten.
- **R-7** Out of scope: passing research or prior-art paths as
  variables to the judge graph; semantic or embedding retrieval;
  relocating `prior_art.py`; any change to `prior_art_gate.py` or the
  pre-commit marker rule; changes to judge doctrine or the judge graph;
  new schema columns; prompt or persona rewrites beyond consuming the
  existing `committed_context`.
- **R-8** The floor's effect on the *notification* consumers is
  recorded, not fixed here. 4 of the 9 most recent FR filenames
  retrieve nothing, and `prior_art_gate.py` fails a commit only when
  hits exist — so for roughly half of new FRs the disposition
  requirement silently evaporates and the Judge's prior-art ground is
  unserved. Recalibrating an interrupting hook is a different
  trade-off (alarm fatigue) and belongs in a follow-up FR. This FR
  supplies the measurement that follow-up needs.
- **R-9** `examples/demos/research-route/graph.yaml` is a governed
  graph artifact. The R-5 wiring must go through the graph-authoring
  route (`scripts/author.sh`) and produce its
  `tmp/draft-authoring-report.md`; unsentineled manual graph writes are
  not authorized. (Judgement C-2.)

## Acceptance Criteria

- **AC-01** `build_prior_art(path)` preserves current hook behaviour
  with `rare_floor=True`: a high-frequency-only fixture returns `""`,
  the existing FR-737/FR-738 ranking, status and self-exclusion tests
  still pass, and `prior_art_gate.py` still calls the default form.
- **AC-02** `build_prior_art(path, rare_floor=False)` returns ranked
  `TOP_N` hits for a fixture corpus in which every matching noun
  exceeds `RARE_MAX_FILES`, preserving status tags, `_weighted_zone`
  ranking, cluster boost, self-exclusion and filename-only extraction.
  This is the regression pin for measurement A.
- **AC-03** `collect_committed_context(repo_root, brief_path)` emits
  `### Prior art retrieved for this brief (filename-noun, IDF-ranked)`
  and searches the synthetic `feature-requests/<brief-stem>.md` path —
  proven by a fixture where the brief's own directory holds tempting
  hits and the emitted hits come from `feature-requests/`.
- **AC-04** A fixture corpus containing a REJECTED FR asserts the block
  carries that filename with its `[REJECTED]` tag, preserving the
  FR-737 rule the Judge enforces.
- **AC-05** Empty retrieval is explicit end to end: with no matching
  noun, `collect_committed_context` emits `none-retrieved`,
  `write_alternatives` writes the same token in the header, and a
  non-librarian row may use `none-retrieved` only under that header.
- **AC-06** The context block stays under `_MAX_CONTEXT_LINES` with a
  full five-hit block, and the existing overflow `ValueError` still
  fires when the bound is exceeded.
- **AC-07** `write_alternatives` copies the prior-art subsection out of
  `state["committed_context"]` into the artifact header byte-for-byte;
  a unit test compares the two slices exactly (R-5).
- **AC-08** Both validators reject a non-librarian precedent cell with
  no committed identifier, no URL and no valid `none-retrieved`; accept
  all three permitted forms; reject `brief-echo` in newly generated
  artifacts; and leave librarian URL and error-string checks unchanged.
- **AC-09** The frozen `TABLE_COLUMNS`/`COLUMNS` tuples and the
  class/verdict enums are byte-identical after the change; the existing
  schema-mirror tests pass untouched.
- **AC-10** A live `scripts/research.sh` run on this FR's own brief
  produces an artifact whose header carries the retrieval block, whose
  non-librarian precedent cells satisfy AC-08, and whose run is logged
  to `feature-requests/research-runs.jsonl`. Success is measured
  against the Problem section's baseline: the run must surface at least
  one FR identifier that appears in neither the brief nor
  `committed_context` — something no run in the route's history has
  done more than four times in total.
- **AC-11** `feature-requests/TEMPLATE.md` states that the
  `**Prior art:**` disposition line dispositions the hits printed in
  the linked research record, naming that record as retrieval evidence.

## Testing

Deterministic unit tests, fixture corpora in `tmp_path`, no network and
no LLM: AC-01/AC-02 in `.github/hooks/tests/`, AC-03 through AC-09 in
`tests/unit/test_fr890_research_route.py` and
`tests/unit/test_fr896_precedent_traceability.py`. AC-10 is the live
demo run; its log is the demo-gate artifact. Full suite:
`pytest tests/unit/ -q --no-cov -m "not slow" -n auto`.

## Risks

- **Context drift.** Five extra grounded lines change persona output
  for every future run. Mitigated by determinism: the same brief
  filename against the same corpus yields the same block, and the
  block is printed into the artifact so any drift is attributable.
- **Filename-noun recall.** The retrieval is only as good as the brief
  filename. R-1 accepts this: escalating to body extraction requires a
  witnessed miss of *extraction*, and the miss measured here is one of
  *floor calibration*. This FR creates the record in which an
  extraction miss would become visible.
- **Grounding noise.** Lifting the floor admits weakly related hits
  into the context block. Bounded by `TOP_N` = 5 and by IDF ranking,
  which still puts the rarest match first; and every hit is printed
  into the artifact (R-5), so a persona that cites a spurious hit is
  visible to the Judge rather than hidden.
- **Precedent check false failure.** A persona with real precedent that
  is neither an identifier nor a URL now fails validation. The
  `none-retrieved` token is the escape hatch, and R-6 makes it count as
  grounded rather than as an echo, so an honest no-hit run cannot be
  pushed below the `non_echo >= 3` threshold into fabrication.

## Alternatives considered

See [FR-932.research.md](FR-932.research.md). Four of five personas
converged on injecting a deterministic corpus digest into the committed
context; the librarian placed it as standard retrieval-before-generation
practice. The subtractionist proposed the opposite direction — delete
the `precedent` shape check entirely and leave precedent substance to
the Judge, which has corpus access. That is rejected here because it
removes the only mechanical signal about precedent while leaving the
personas just as blind; this FR keeps the check and removes the
blindness that made it hollow. Its warning is honoured in R-6a and in
the `none-retrieved` token: the check must never make fabrication
cheaper than admission.

Noted against this FR's own research run: four of its five rows cite
`FR-890 R-2`, an identifier written in its brief. The run is itself an
instance of the defect it describes.
