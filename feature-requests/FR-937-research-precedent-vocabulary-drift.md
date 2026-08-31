# FR-937: The Research Route's Prompts and Its Validators Disagree About Precedent

**Priority:** HIGH
**Type:** Defect
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-31
**First consumer / first event:** `scripts/research.sh`, at the next run on a
subject with no committed precedent — the sole research route for the whole
repository, which currently cannot complete such a run at all.
**Research:** [FR-937.research.md](FR-937.research.md) — produced by
`scripts/research.sh` on
`feature-requests/research-briefs/fr-937-precedent-vocabulary-drift-brief.md`.
The graph exited 0 with five valid rows and five prior-art hits; the record
was promoted by hand because the artifact preflight then rejected it on a
false positive that is itself an instance of this defect, folded in below as
W-3. Header records the deviation.
**Prior art:** `FR-896-research-route-precedent-traceability.md` froze the
precedent contract and originally defined the `brief-echo` demotion this FR
finishes retiring — direct territory, not distinguished.
`FR-932-prior-art-retrieval-in-research-route.md` introduced `none-retrieved`
and the retrieval block, and shipped the precedence defect in W-3 — this FR
completes FR-932's own change. `FR-890-...-closed-input-alternatives.md`
established the closed brief and the persona schema; unchanged here.
`FR-933-retry-cannot-recover-deterministic-rejection.md` is adjacent — same
route, but a schema rejection inside an LLM node; this failure is raised by a
python reducer, so no retry path applies and nothing in FR-933 addresses it.
`FR-592-perspective-vocab-extraction-stage.md` (REJECTED) and FR-583/584/593
were retrieved on the nouns "vocabulary" and "drift" but concern
story-modelling vocabulary in the plot-modeller pipeline — subject-unrelated,
distinguished.

**Depends on:** PR #525 (FR-938 + FR-933). `none-retrieved`, the retrieval
block, and `_check_precedent` do not exist on `main` yet. This branch must
rebase onto `main` after #525 merges. (FR-938 was authored as FR-932 and
renumbered after a parallel session landed `FR-932-lukiot-csv-extraction.md`;
the judgement below cites the old number.)

## Judgement disposition

[FR-937-research-precedent-vocabulary-drift.judgement.md](FR-937-research-precedent-vocabulary-drift.judgement.md)
returned **SPLIT** with six required revisions. Operator ruling, 2026-08-31:
**fold the corrections, do not split, do not re-judge.** R-3, R-4, R-5, R-6 and
R-7 are folded into the constraint and criteria below verbatim in substance —
they found four real defects in this document (a symbol that does not exist,
the librarian's URL-only contract, the wrong seam for W-5, and a stale
capability text). R-1 (three-way split) and R-2 (re-entry with fresh research)
are overridden: the three seams share one incident chain, one live witness, and
one reviewer, and splitting them triples the merge cost that the operator has
named the repository's primary handicap. Recorded honestly against R-2: the
research record carries three solution classes, not the doctrine's four to six;
four of five personas converged, which is the finding, not a shortfall to be
papered over.


## Summary

Two halves of the research route hold different beliefs about what a persona
may write when it has no precedent to cite. The prompts sanction a marker the
reducer kills the run for, and never name the one marker the reducer accepts.
A second pair — the reducer and the artifact preflight — implement the same
rule with opposite precedence. Each half is internally consistent; the policy
connecting them is not.

## Root cause

FR-896 defined `brief-echo:` as a demotion: the row is retained but excluded
from scoring. FR-932 retired it — restating the brief as its own precedent is
not precedent — and replaced it with a bounded `none-retrieved` claim,
verifiable against the retrieval block the personas were actually shown.

The replacement landed in the reducer. It never reached the prompts.

```
grep -l "brief-echo"     examples/demos/research-route/prompts/*.yaml  → 5 of 5
grep -l "none-retrieved" examples/demos/research-route/prompts/*.yaml  → 0
```

A persona holding no precedent has exactly one instruction available, that
instruction is sanctioned in writing by its own system prompt, and obeying it
raises from `reduce_findings` and exits the graph non-zero. The accepted
escape is unreachable from the prompt; the reachable one is fatal.

Separately, `research_preflight._check_precedent` tests
`NONE_RETRIEVED in citation` **before** it tests for committed identifiers,
while the reducer's `_classify_precedent` tests `_check_committed_ids`
**first** and returns `traceable`. A cell citing three real FRs is therefore
accepted by one and rejected by the other, whenever it happens to name the
marker.

## Violated objective

The route is the sole research route for the repository and the input to every
subsequent judgement. It is currently unable to complete a run on a novel
subject — and novelty is anti-correlated with retrieval, because FR-932
recorded that filename-noun IDF "finds prior art that shares vocabulary and
misses prior art that shares a problem". The route is most reliable on
subjects the corpus already covers, where research is least needed.

## Witnessed incidents

- **W-1** 2026-08-31, brief
  `operator-coffee-physical-actuation-brief.md` (no committed precedent, so
  retrieval was empty). Four personas produced valid rows; the fifth followed
  its instruction and wrote `brief-echo: agent knows when the wait is …`. The
  reducer raised, the graph exited 1, no artifact was written.
  Evidence: [FR-937-evidence.md](FR-937-evidence.md).
- **W-2** Same brief, second run: byte-identical failure, same persona, same
  string. Deterministic at `temperature: 0.0` — re-running is not a
  workaround, and one persona in five is enough to fail the whole fan-out.
- **W-3** 2026-08-31, this FR's own research run. Graph exited 0 with five
  valid rows; `research_preflight.py` rejected the artifact because the
  subtractionist cell `FR-896 (precedent traceability), FR-932 (none-retrieved
  bounded claim), CAP-248 (research sole route)` contains the literal string
  `none-retrieved`. Three committed identifiers, rejected for naming the
  marker under study. Evidence: [FR-937-evidence.md](FR-937-evidence.md).
- **W-4** Same class, brief side: `research_preflight` matches the
  classification enum by substring, so a sentence disclaiming a class counts
  as claiming it — a brief saying "nothing here needs measurement" is rejected
  for naming two classes. Cost one failed run before the route was entered.
- **W-5** Same run: a brief missing a required heading is reported as
  `remove solution-shaped sections from the brief`, naming the opposite of the
  actual fault. The helper itself is innocent — it emits
  `missing or empty required heading` correctly; the wrapper
  `scripts/research.sh` discards it and substitutes its own guess.
- **W-6** 2026-08-31, the demo fixture `tests/fixtures/fr890/clean-brief.md`,
  run to regenerate `examples/demos/research-route/demo-output.log` for the
  demo-proof gate. The yamlgraph-native-planner cited **two real committed
  identifiers and then the marker**:
  `FR-890 research-route graph; CAP-248 research sole route (closed-input
  alternatives); brief-echo: planning phase must gain input closure …`.
  The reducer accepted it — `rows: 5, non_echo_rows: 5, classes: 4`, graph
  rc=0 — and the preflight rejected it, because the reducer resolves
  identifiers first and the preflight tests `ECHO_MARKER` first.

  W-6 is the mirror image of W-3: the same precedence disagreement, reached
  through the *other* marker. It also raises the cost of the status quo from
  inconvenience to blockage — **the research-route demo-proof gate cannot be
  satisfied while this defect stands**, because any change under
  `examples/demos/research-route/` demands a passing demo log the route
  cannot currently produce. The FR-938 renumber had to leave that file's
  comments stale for exactly this reason; this FR clears them.
  Evidence: [FR-937-evidence.md](FR-937-evidence.md).

W-3 and W-4 are one defect class: **a substring match treats a mention as a
claim.** W-1/W-2 are a second: **prose and code drifted apart with no mechanism
to notice.** W-5 is a third and smallest: **a wrapper discards a correct
diagnosis and substitutes a guess.** W-6 shows the first class is not one-sided:
both markers are affected, in opposite directions, by the same disagreement
about what to resolve first.

## Ideal Result

A persona that has no precedent writes the one thing that is both true and
accepted, because its prompt says so; and no rule of the precedent contract
exists in two places where it can drift again.

## Proposed constraint

Minimal path back from that end state:

1. **The prompts stop naming a fatal marker and start naming the accepted
   one.** All five persona prompts drop the `brief-echo:` paragraph. The four
   internal personas gain the `none-retrieved` claim together with its
   precondition — claimable only when the retrieval block shown to the persona
   was empty. **The librarian gains nothing**: its contract is a real URL
   copied from tool results, it has no internal honest-miss escape, and that
   rule is not weakened (R-3). Authored through `scripts/author.sh`; these are
   governed artifacts under FR-767.
2. **The reducer keeps rejecting `brief-echo`.** It becomes a guard against a
   marker nothing instructs any more, not a trap under a live instruction.
3. **One precedence, not two.** Both validators resolve committed-identifier
   and URL shapes **before** marker classification, so a cell citing real
   precedent stays `traceable` whatever words it also contains. The reducer
   keeps its stronger filesystem-existence check; agreement is about
   precedence and marker semantics, not about pretending a shape check proves
   existence (R-4).
4. **A marker is a claim, not a substring.** `none-retrieved` and `brief-echo`
   are recognised only when the stripped precedent cell *equals* the marker or
   *begins with* `<marker>:`. An occurrence anywhere else is prose. The same
   rule governs the brief's classification: the claim is the leading enum
   token of the first non-empty line of `## Classification`, terminated by
   end-of-line or the documented delimiter; later explanatory prose is not
   scanned (R-6).
5. **A test holds the two halves together.** Not a natural-language extractor:
   five exact contract witnesses (AC-02) that fail if either a prompt marker
   or its code constant is edited alone.
6. **The wrapper stops guessing.** `scripts/research.sh` retains
   `research_preflight.py`'s specific violations and adds only a neutral
   summary; the misleading `remove solution-shaped sections` diagnosis is
   deleted from the wrapper, not from the helper, which was already correct
   (R-7).
7. **The capability text catches up.** `CAP-248` / `REQ-YG-623` still says
   `brief-echo` is demoted and preserved. It is rewritten to the bounded
   `none-retrieved` rejection semantics (R-5).

The `is_this_a_graph` answer is no: this is a contract reconciliation between
two artifacts in two languages, not a task shape. Four of five personas
converged on (1); the librarian's external precedent
(https://opencode.ai/v2/docs/compaction — compare live instruction sources
against admitted values before each attempt) is the argument for (5). The
os-infra-primitivist's compile-time variant is dispositioned as rejected
below.

### Rejected alternative, recorded

**Move the precedent check into the YAML schema validator at compile time**
(os-infra-primitivist). The check is not decidable at compile time: whether
`none-retrieved` is legitimate depends on the retrieval block produced at
run time for that specific brief. A compile-time gate could only check the
*shape* of the cell, which is `gate_checks_shape_not_substance`. Rejected.

## Acceptance criteria

Numbering follows the judgement's revised list where it applies.

- **AC-01** RED: all five persona prompts omit `brief-echo`; exactly the four
  internal persona prompts carry the canonical bounded `none-retrieved`
  instruction; `librarian_structure.yaml` carries neither an internal
  honest-miss escape nor a weakened URL rule.
- **AC-02** RED, anti-drift: the canonical prompt marker string and the code
  constant are asserted against each other, such that editing either alone
  fails. No natural-language extraction — exact tokens only.
- **AC-03** Shared truth table. One table of precedent cells is run through
  **both** `research_tools._classify_precedent` and
  `research_preflight._check_precedent`, and they agree on accept/reject for:
  (a) a committed citation whose prose mentions `none-retrieved` — the W-3
  regression, using the verbatim cell from FR-937-evidence.md; (b) a
  committed citation whose prose ends in `brief-echo: …` — the W-6 mirror,
  using the real cell from the demo fixture run; (c) a bare `none-retrieved`
  claim with empty retrieval; (d) the same claim with non-empty retrieval;
  (e) a cell that is only `brief-echo: …`; (f) prose-only precedent;
  (g) a fabricated identifier. The reducer additionally enforces filesystem
  existence; that asymmetry is intended and asserted, not removed.
- **AC-04** A marker is claimed only when the stripped cell equals the marker
  or begins with `<marker>:`; a cell merely containing it elsewhere is
  classified by its other content.
- **AC-05** FR-938's bound is not weakened: `none-retrieved` with non-empty
  retrieval is still rejected by both, and fabricated identifiers stay fatal.
- **AC-06** `CAP-248` / `REQ-YG-623` is rewritten from `brief-echo` demotion
  to bounded `none-retrieved` rejection semantics.
- **AC-07** Prompt changes are produced by `scripts/author.sh` with
  `tmp/draft-authoring-report.md` recording governed files, lint, smoke and
  limitations. No hand-edit of any file under
  `examples/demos/research-route/prompts/` or of `graph.yaml`.
- **AC-08** Live witness, three briefs: `scripts/research.sh` on the W-1 brief
  `operator-coffee-physical-actuation-brief.md` (empty retrieval), on this FR's
  own brief (non-empty retrieval), and on the W-6 demo fixture
  `tests/fixtures/fr890/clean-brief.md` each exit 0, produce five persona rows,
  pass artifact preflight, and append a provenance line to
  `feature-requests/research-runs.jsonl`. The first has never succeeded; the
  third regenerates `examples/demos/research-route/demo-output.log`, unblocking
  the demo-proof gate, and the code comments FR-938 had to leave stale are
  renumbered in the same change.
- **AC-09** Classification claim parsing: a brief whose classification line
  carries one enum token followed by prose that mentions or disclaims another
  is accepted; zero, unknown, or two claim-position enums are rejected. No
  other brief-closure check (forbidden headings, candidate bullets, required
  headings) changes behaviour.
- **AC-10** Wrapper diagnostic: a subprocess test drives `scripts/research.sh`
  with a missing-heading brief and asserts exit 64, the exact
  `missing or empty required heading` diagnostic reaching the operator, and
  the absence of `remove solution-shaped sections`.
- **AC-11** New tests carry `@pytest.mark.req("REQ-YG-623")`; a changelog
  fragment exists; this FR gains an implementation-status section; a diary
  reflection is added.
- **AC-12** Base: this branch is rebased onto `main` after #525 lands, so RED
  runs against symbols that exist.

## Out of scope

Changing what counts as precedent; weakening FR-938's `none-retrieved` bound,
the identifier rule, or the librarian's URL rule; changing `max_length=400` or
the rejection-never-truncation contract; changing the retrieval ranking, the
floor, or the corpus; adding a persona or a schema column; compile-time
precedent validation (dispositioned above); graph topology; the open question
of whether an LLM pass over the FR corpus should replace filename-noun
retrieval (recorded in FR-938, its own FR); changing the judge, authoring,
review, CI or hook routes.

## Implementation status

**Enforced.** All acceptance criteria met on branch
`feat/fr937-research-precedent-vocabulary`, rebased onto `main` at `a5012228`
(AC-12 — #525 landed first, so RED ran against symbols that exist).

### What changed

- `scripts/research_preflight.py` — `is_marker_claim(citation, marker)` replaces
  naive `in` matching: a marker counts only as the whole cell or as a leading
  `marker:` prefix. `_check_precedent` accepts a bounded `none-retrieved` claim
  only when the retrieval block came back empty, and rejects the retired
  `brief-echo` marker outright. `_check_classification_claim` requires the
  claimed enum value to lead the first non-empty line and be followed by a
  delimiter, so a mention inside prose no longer scores. `check_brief` calls it.
- `examples/demos/research-route/nodes/research_tools.py` — the same
  `is_marker_claim` predicate, so the reducer and the preflight share one
  contract rather than implementing it twice. Stale `FR-932` comments renumbered
  to `FR-938`.
- `scripts/research.sh` — the closure failure message now reports the violations
  actually found instead of asserting "remove solution-shaped sections".
- `examples/demos/research-route/prompts/*.yaml` — re-authored through
  `scripts/author.sh` (FR-767 sole route; report at `tmp/draft-authoring-report.md`,
  graph lint exit 0, narrow smoke run produced `tmp/draft-alternatives.md`). The
  four internal personas are taught the bounded `none-retrieved` marker; both
  librarian prompts keep their URL-only contract and gained no honest-miss escape.
- `capabilities/CAP-248-research-sole-route.yaml` — `REQ-YG-623` rewritten from
  the retired `brief-echo` demotion semantics to the bounded `none-retrieved`
  rejection semantics actually enforced (AC-06).

### Verification

- `tests/unit/test_fr937_precedent_vocabulary.py` committed RED first
  (9 failures, one per criterion), then GREEN. Full suite with FR-938 and
  FR-896: **72 passed**.
- Live witnesses (AC-08), all exit 0, five rows, artifact preflight ok,
  provenance appended to `feature-requests/research-runs.jsonl`:
  - `operator-coffee-physical-actuation-brief.md` — the empty-retrieval brief
    that had **never** completed before this fix. Now `rows: 5, classes: 3`.
  - `fr-937-precedent-vocabulary-drift-brief.md` — non-empty retrieval,
    `rows: 5, classes: 3`.
  - `tests/fixtures/fr890/clean-brief.md` — `rows: 5, classes: 4`, redirected to
    `examples/demos/research-route/demo-output.log`, unblocking the demo-proof
    gate that had held the FR-938 renumber hostage.

### Deviations from the judgement

Recorded in full under "Judgement disposition" above. R-1 (three-way split) and
R-2 (re-entry) were overridden by the operator: one FR, corrections folded, no
re-judge. R-3 through R-7 — the four substantive defects the judge found by
reading the code — were folded verbatim in substance.

### Defect found during enforcement

The acceptance test's own `INTERNAL_PROMPTS` selector excluded
`librarian_structure.yaml` by exact filename, silently classifying the second
librarian prompt (`librarian.yaml`) as an internal persona. Corrected to exclude
every librarian prompt by substring, matching the `is_librarian()` predicate the
production code already uses — the same naive-matching family this FR exists to
cure, reproduced in its own test.
