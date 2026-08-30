# Feature Request: Prior-art retrieval inside the research route

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-30
**First consumer / first event:** the Judge, at the next
`scripts/judge.sh` run on an FR created after this lands — it opens
`feature-requests/FR-NNN.research.md` and reads a retrieved,
status-annotated prior-art block at the head of the table instead of
inferring precedent from persona prose.
**Research:** [FR-932.research.md](FR-932.research.md)
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

Measured over the twelve committed research artifacts (60 rows): 33
precedent cells name an `FR-`/`NC-`/`CAP-`/`REQ-` identifier, 12 carry
a URL (the librarian rows), and 15 carry neither — a quarter of all
rows clear the non-empty shape check while citing nothing that can be
looked up. Twelve cells prefix `brief-echo:` and restate the brief as
its own precedent. This is `gate_checks_shape_not_substance` on the one
column whose whole purpose is substance.

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

The first draft of this FR proposed reusing `build_prior_art` verbatim.
Running it before freezing the design killed that mechanism
(`read_raw_output_first`). Querying the 854-file `feature-requests/`
corpus with each of the 14 committed research-brief filenames:

| query filenames | hits returned | silent |
|---|---|---|
| 14 research briefs | 3 | **11** |
| 9 recent FR filenames (FR-920…929) | 5 | **4** |

This brief's own filename (`prior, art, precedent, brief`) returns
**nothing** against the FR corpus, while returning five hits against
the 13-file `research-briefs/` directory.

The cause is `RARE_MAX_FILES = 20`, an absolute floor: a noun counts as
rare only if it appears in ≤ 20 files. At 854 files that is 2.3%, so
any noun with ordinary currency in this repo is disqualified and
`build_prior_art` returns `""`. FR-737 F2+A1 predicted exactly this in
its own comment — "absolute; ≈3% today, tightens as the corpus grows".
This is the witnessed miss `two_strike_split` and FR-737 F4 required
before the retrieval may be changed.

The distinction the numbers force: **the rarity floor is a notification
policy, not a retrieval policy.** It exists so an advisory hook that
interrupts an author stays silent rather than crying wolf. A grounding
block inside a research run interrupts nobody — an irrelevant line in a
context window costs far less than a missing precedent. The two
consumers need the same ranking and different floors.

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
context, `verify_artifact` requires each non-librarian `precedent` cell
to contain a repo identifier `(FR|NC|CAP|REQ)-\d+`, a URL, or the
literal token `none-retrieved`. Prose-only precedent fails the shape
check. The explicit token is what a persona writes when it genuinely
has no precedent — an honest miss must remain cheaper than fabricating
a citation.

## Requirements (frozen on judgement)

- **R-1** The only change to `prior_art.py` is one keyword argument,
  `rare_floor: bool = True`, gating the existing `rare` early return.
  Noun extraction is NOT extended: FR-737 F4 purged title/body
  extraction and the miss measured above is a floor-calibration miss,
  not an extraction miss. The module is not relocated.
- **R-1a** Both existing callers (`fr-checks.sh` advisory,
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
  returns `""` — with the floor lifted this means no noun matched any
  file at all — both the context block and the report carry
  `none-retrieved`.
- **R-5** The retrieval block is written verbatim into the research
  artifact header. No new column; the frozen column set stands.
- **R-6** The tightened precedent check is prospective. The twelve
  committed research artifacts are not retro-gated.
- **R-7** Out of scope: passing research or prior-art paths as
  variables to the judge graph; semantic or embedding retrieval over
  the corpus; relocating `prior_art.py`; any change to
  `prior_art_gate.py` or the pre-commit gate's marker check.
- **R-8** The floor's effect on the *notification* consumers is
  recorded, not fixed here. 4 of the 9 most recent FR filenames
  retrieve nothing, and `prior_art_gate.py` fails a commit only when
  hits exist — so for roughly half of new FRs the disposition
  requirement silently evaporates and the Judge's prior-art ground is
  unserved. Recalibrating the floor is a different decision with a
  different trade-off (alarm fatigue on an interrupting hook) and
  belongs in a follow-up FR. This FR supplies the measurement that
  follow-up needs.

## Acceptance Criteria

- **AC-01** `collect_committed_context` accepts a brief filename and
  emits a `### Prior art retrieved` sub-section; unit test asserts the
  section is present and that its hits are drawn from
  `feature-requests/`, not from the brief's own directory.
- **AC-02** Unit test with a fixture corpus asserts a REJECTED FR
  appears in the block with its `[REJECTED]` status tag — the FR-737
  precedent rule the Judge enforces is visible to the personas.
- **AC-03** Unit test asserts `none-retrieved` appears in both the
  context block and the artifact header when the retrieval returns
  empty (R-4).
- **AC-03a** Regression test pins the measured miss: a corpus where
  every matching noun exceeds `RARE_MAX_FILES` returns `""` with the
  default and returns ranked hits with `rare_floor=False`. Separate
  tests assert the two existing callers still receive the floored
  result.
- **AC-04** Unit test asserts the emitted context stays under
  `_MAX_CONTEXT_LINES` with a full five-hit block, and that the
  existing overflow `ValueError` still fires when the block would
  exceed it.
- **AC-05** `verify_artifact` rejects a non-librarian row whose
  precedent cell has no identifier, no URL and no `none-retrieved`
  token; accepts each of the three permitted forms. Existing librarian
  URL and error-string checks are unchanged (witnessed by the current
  tests still passing).
- **AC-06** The frozen `COLUMNS` tuple and the class/verdict enums are
  byte-identical after the change; the existing schema-mirror test
  between `research_preflight.py` and `research_tools.py` passes
  untouched.
- **AC-07** A live `scripts/research.sh` run on this FR's own brief
  produces an artifact whose header carries the retrieval block and
  whose non-librarian precedent cells all satisfy AC-05, and the run is
  logged to `feature-requests/research-runs.jsonl`. The log line and
  artifact are the demo evidence.
- **AC-08** `feature-requests/TEMPLATE.md` states that the
  `**Prior art:**` disposition line dispositions the hits printed in
  the research record, naming that record as the retrieval evidence.

## Testing

New tests in the research-route test module (fixture corpus in
`tmp_path`, no network, no LLM): AC-01 through AC-06 are all
deterministic stdlib assertions. AC-07 is the demo run; its output log
is the demo-gate artifact. Full suite:
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
  is neither an identifier nor a URL now fails the shape check. The
  `none-retrieved` token is the escape hatch, and it is honest — it
  says the persona found nothing rather than dressing prose as a
  citation.

## Alternatives considered

See [FR-932.research.md](FR-932.research.md). Four of five personas
converged on injecting a deterministic corpus digest into the committed
context; the librarian placed it as standard retrieval-before-generation
practice. The subtractionist proposed the opposite direction — delete
the `precedent` shape check entirely and leave precedent substance to
the Judge, which has corpus access. That is rejected here because it
removes the only mechanical signal about precedent while leaving the
personas just as blind; this FR keeps the check and removes the
blindness that made it hollow. Its warning is honoured in R-6 and in
the `none-retrieved` token: the check must never make fabrication
cheaper than admission.
