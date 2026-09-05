# Feature Request: Module-History Demo — YAMLGraph Witness for the Phased Summary Pattern

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-04). R-1..R-7 folded
below. Authority remains **inactive** pending human confirmation of the fold
(judgement C-1); no implementation is authorized. Amended 2026-09-04 with two
post-merge factual corrections — see § Amendment and § Judgement history.
**Effort:** 1 day
**Requested:** 2026-09-04
**First consumer / first event:** the agent or human onboarding onto an
unfamiliar module, at the moment they ask "what happened to this file and
why" — today answered by `git log -p` and a fresh read of 200 commits. The
second consumer is the reader of `reference/patterns/phased-summary.md`, at
the moment they ask whether the pattern has ever been run.
**Research:** [FR-981.research.md](FR-981.research.md) — FR-890 sole route,
`scripts/research.sh` run 2026-09-04T03:06:20Z over
`feature-requests/research-briefs/fr981-phased-summary-witness-brief.md`,
five personas, six solution classes folded. Provenance line in
`research-runs.jsonl`; `--verify-artifact` on the appendix passes,
`--verify-promotion` reports `mismatched` on the known Windows CRLF
discrepancy documented in the record header.
**Prior art:**
- **External, and the reason this FR was revised:** CLIN-SUMM
  ([medRxiv](https://www.medrxiv.org/content/10.64898/2025.11.28.25341233v3.full))
  independently implements all four properties over clinical notes —
  retained per-note summaries in a Parquet store, two-prompt incrementality,
  Jaccard redundancy filter, sliding window, with measured savings *and*
  measured completeness. POMR (Weed 1964; NEJM 1968) is the paper ancestor.
  DISTINCT from this FR: neither is a YAMLGraph composition, and the clinical
  corpus is unusable here. Both are ADOPTED as design input, not duplicated.
- [FR-611 / FR-612 / FR-613 / FR-614 roundtrip skeleton](FR-611-roundtrip-skeleton-p1-cast-briefs.md)
  and [FR-852-preserve-authoring-briefs.md](FR-852-preserve-authoring-briefs.md)
  — the hits the research route's retrieval returned on the nouns "phased",
  "summary", "brief". DISMISSED as `false_duplicate`: plot_modeller chapter
  briefs are *authored planning* artifacts written to generate prose, and
  FR-852's briefs are task inputs to `scripts/author.sh`. Both run the
  opposite direction from a brief that compresses an existing record.
- [FR-775-book-summary-loop-redesign.md](FR-775-book-summary-loop-redesign.md)
  — closest precedent: per-page brief plus one LLM reduction. DISTINCT: its
  page summaries are discarded scaffolding, there is no subject axis, and a
  second run recomputes everything. This FR adds exactly the three things it
  lacks — durable store, subject grouping, incremental cost — and reuses its
  map-plus-reduce shape unchanged.
- [FR-773 / FR-774 book-summary demo + splitter](FR-774-book-summary-scale-hardening.md)
  — the batching and cursor mechanics are precedent for windowing a long
  record list; not re-implemented here (git history needs no splitter).
- [FR-892-corpus-census-pipeline-injected-adapters.md](FR-892-corpus-census-pipeline-injected-adapters.md)
  — the slot-bound census pipeline. DISTINCT and dispositioned in
  Alternative A: census has no per-item durable store, no invalidation rule,
  and its synthesize tail (FR-895) produces a corpus-level brief, not a
  per-subject rollup. Reusing it would require changing its contract.
- [FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md)
  — nearest *subject-scoped* precedent (unit = PR, reduce target = one
  person). DISTINCT: single-shot profile over a date window; no brief is
  retained and the next window pays full price. If this FR is enforced,
  FR-962 becomes a candidate consumer of the store, not a duplicate.
- [FR-616 compaction pattern](../reference/compaction-pattern.md) — same
  compression move, scoped to one running graph; transient by design.
- [FR-254 diary_index demo](../examples/demos/diary_index/README.md) — map
  over a file corpus into a deterministic aggregate. DISTINCT: aggregation is
  Python and there is no LLM rollup; also full recompute per run.
- [FR-819-github-native-digest-poc-repo.md](FR-819-github-native-digest-poc-repo.md)
  — git-native digest precedent; time-window digest, not subject dossier.

## Summary

Add `examples/demos/module-history`: a demo that reduces every commit touching
a source module to one durable typed brief, keeps those briefs in a
content-addressed store, and builds the module's dossier from briefs alone.
Running it a second time after one new commit costs one brief call, and the
demo proves that number rather than claiming it.

The claim is deliberately narrow, and narrower than the first draft's. The
*shape* needs no witness from this repository: CLIN-SUMM already implements
and measures it, and POMR predates it by sixty years. What is unexercised is
the **YAMLGraph composition** — that these phases compose here, that the
retention boundary sits where the research says it sits, and that the
incremental cost is what the pattern claims. That is what this demo
witnesses.

**The pattern document does not exist in the repository (R-1).** Enforcement
*creates* `reference/patterns/phased-summary.md` and adds its
`reference/README.md` index row; both are deliverables, not existing claims
being repaired. An uncommitted working-tree draft exists in the authoring
worktree and carries no authority. The grades that document must state are
fixed here in advance: the *shape* is externally evidenced at **preprint
grade** (CLIN-SUMM) plus one operator report, and the *YAMLGraph composition*
stays **UNEXERCISED** until AC-04 and AC-08 pass.

## Value Statement

A developer evaluating YAMLGraph sees a pattern documented with one external
anecdote; after this FR they can run it, read the store on disk, add a commit,
and watch the incremental cost be one call. The repository gets the same thing
it gives the reader: a module dossier that is cheaper to keep current than to
regenerate.

## Problem

1. **The composition has no runnable witness, and no document either.** The
   pattern this project would publish has neither a committed description nor
   a graph that runs it. The shape is
   externally proven — that part of the first draft's problem statement was
   wrong and the research route corrected it — but a reader of a YAMLGraph
   pattern document is asking whether it composes *here*, and no committed
   graph answers that. `demo_vs_test`: demos prove the abstraction is worth
   having.
2. **The distinguishing properties are the untested ones.** Map-plus-reduce is
   precedented five times over. The store, the invalidation rule, and the
   incremental call count are precedented zero times — which is exactly why
   the demo must assert them mechanically rather than narrate them in a
   README. **[Corrected 2026-09-04 — see § Amendment: the store and the
   reference gate are precedented twice. The surviving unexercised claims are
   substitution, the subject rollup, version invalidation, and counted
   incremental cost.]**
3. **The repository has the problem the pattern solves.** Onboarding onto a
   module means reading its history; `git log` returns transport fragments,
   and asking a model to read 200 diffs is the
   `impossibly_large_sequential_task` framing with no store to amortise it.

## Amendment 2026-09-04 — two factual corrections found after merge

Filed without re-judgement: this corrects claims of fact and does not widen
scope, allocate identifiers, or activate authority. The judgement's gates
C-1..C-8 stand unchanged. Correction 2 does bear on the frozen architecture,
and is recorded as a question owed to enforcement rather than resolved here.

Both errors have one root. A pattern check keyed on *mechanism* rather than
on the vocabulary of summarisation found in minutes what this FR's manual
sweep, its five-persona research route, and two judge executions all missed.
Reflected on in
[docs/diary/diary-2026-09-04-reflection-the-vocabulary-i-searched-with.md](../docs/diary/diary-2026-09-04-reflection-the-vocabulary-i-searched-with.md).

### Scope note — the pattern document was committed early, by operator decision

R-1 and AC-14 make `reference/patterns/phased-summary.md` an enforcement
deliverable, and the judgement's not-authorized list names it explicitly. The
operator directed it to be committed with this amendment instead. Recorded
here rather than glossed: the judgement's frozen surface was crossed
deliberately and by the human the C-1 gate names, not by the author acting
alone.

The document as committed carries both corrections below — its evidence grade
now reads PARTLY EXERCISED, distinguishing the store and gate (committed and
working) from substitution, the subject rollup, version invalidation, and
counted incremental cost (unexercised). AC-14 therefore survives as a
narrowed obligation: enforcement must move that composition grade and name
the demo once AC-04 and AC-08 pass, rather than create the document.

### Correction 1 — the durable store is precedented twice, not zero times

§ Problem 2 states that the store, the invalidation rule, and the incremental
call count are "precedented zero times". Two committed graphs contradict the
first two:

- [`examples/demos/wiki-memory`](../examples/demos/wiki-memory/README.md)
  (CAP-173/CAP-174; FR-625, FR-628, FR-629, FR-120) writes `wiki/<id>.yaml`
  per page via `write_data_file`, reads the accumulated set back through a
  `data_files` glob on later runs, and gates persistence on a Python node that
  rejects any page whose references do not resolve — the same contract this FR
  calls invariant 5 and treats as a novel testable claim.
- [`examples/novel_fandom`](../examples/novel_fandom/README.md) (CAP-181;
  FR-655) keeps `canon/character/*.yaml` and `canon/event/*.yaml` under a
  no-orphan-reference gate **and** a lane-immutability rule barring the model
  from overwriting `lane: static` pages — an authority rule over stored
  artifacts, adjacent to this FR's version-invalidation concern.

The novelty claim narrows accordingly, and the surviving claim is still
sufficient to justify the demo: **substitution** (a brief standing in for its
source in later prompts), the **subject-scoped rollup**, **version-keyed
invalidation**, and the **counted incremental cost** remain unexercised in
this repository. The store and the reference gate do not.

Enforcement consequence: reuse `write_data_file` and `data_files` rather than
hand-rolling a store, and cite both witnesses in the demo README.

### Correction 2 — "the store is not a graph" is contradicted by the witnesses

§ Alternatives Considered concludes *"the phases are; the store is not"*, on
four of five research rows answering `is_this_a_graph: No`. A second sole-route
run, pointed at the two witnesses above, returned four of five answering
**Yes**: the durable store is expressible in YAML, because `write_data_file`
persists the keyed artifact, the `data_files` glob reads it back, and the
gates are `type: python` **nodes inside the graph** rather than code beside it.
Record:
[docs/2026-09-04-research-durable-keyed-artifact-store.md](../docs/2026-09-04-research-durable-keyed-artifact-store.md).

The difference is method, not opinion: this FR's route reasoned about the
framework in the abstract and about `book-summary`'s per-run `all_summaries`
reducer; the second route read graphs that already do it.

This FR's answer is therefore **withdrawn as overstated**. It is not replaced
with the opposite claim here, because § Proposed Solution's Python-owned
`plan_briefs`/`persist` design rests on it and that design is frozen by the
judgement. **Owed at enforcement:** determine whether the store is expressible
with `write_data_file` + `data_files` for this demo, and if it is, return to
Plan for a scope revision rather than hand-rolling `tools.py` persistence
under a superseded premise. AC-10's contracts hold either way.

## Judgement history

**2026-09-04, first judge execution — REJECTED, returned to Plan** on the
committed-input boundary: the FR, its research record, and the brief were all
uncommitted, so the judge could evaluate no substance. Artifact:
`tmp/draft-judgement.md`. Dispositions:

- **R-1 (commit the closed planning record) — DONE.** This FR, the research
  record, the brief, and the `research-runs.jsonl` provenance line were
  committed as a planning-only commit. `reference/patterns/phased-summary.md`
  and `reference/README.md` were deliberately excluded per the judge's
  not-authorized list; they remain uncommitted working-tree drafts, which is
  why this FR cites the pattern doc as a proposal rather than as evidence.
- **R-2 (make `--verify-promotion` report a match) — NOT SATISFIABLE IN THIS
  SCOPE; evidence below.** The verdict treats the mismatch as this FR's
  defect. It is repository-wide and predates this FR. `scripts/research.sh:76`
  hashes the artifact's **raw bytes**, which on this Windows host are CRLF
  because the graph writes the file in Python text mode;
  `research_preflight.verify_promotion` hashes the record read through
  `read_text()`, which normalizes to LF. The two digests cannot agree for any
  byte-faithful promotion, in either direction. Committed precedent:
  `python3 scripts/research_preflight.py --verify-promotion
  feature-requests/FR-955.research.md feature-requests/research-runs.jsonl`
  reports `mismatched` today, on a record that was judged and enforced. The
  two available fixes are (a) make the route write LF, which is a change to
  research tooling that this FR's scope and the judge's own not-authorized
  list both forbid, or (b) rewrite the recorded digest in
  `research-runs.jsonl`, which would falsify the launcher's own attestation
  to make a verifier pass. Neither is taken. The content *is* verified:
  `--verify-artifact` on the appendix passes. **Owed:** a separate FR fixing
  the newline boundary in the research route — same defect class as FR-951.
- **R-3 (re-enter judgement from the committed revision) — DONE.**

**2026-09-04, second judge execution — APPROVED WITH REVISIONS**, on commit
`afa14b80`. Judgement:
[FR-981-module-history-phased-summary-demo.judgement.md](FR-981-module-history-phased-summary-demo.judgement.md).
Strategic classification: contrib/example with pattern documentation — not a
framework primitive, not a new capability. R-1..R-7 are folded into this
revision:

| # | Revision | Where folded |
|---|---|---|
| R-1 | Enforcement *creates* the pattern document; grades fixed in advance | § Summary, § Problem 1, AC-14 |
| R-2 | One selected record to exactly one brief; near-duplicate filter deleted | § Proposed Solution, AC-07 |
| R-3 | One path per invocation, frozen window, honest ceilings | § Proposed Solution, AC-05/AC-06 |
| R-4 | Collision-resistant subject key, validated envelope, typed claims | § Proposed Solution, AC-10/AC-11 |
| R-5 | Exact call arithmetic including the unchanged third run | AC-08, AC-09 |
| R-6 | Pre-authority raw read plus a frozen cost/loss protocol | [FR-981-pilot-raw-read.md](evidence/FR-981-pilot-raw-read.md), AC-12 |
| R-7 | Committed authoring brief; no CAP/REQ allocation | § Proposed Solution, AC-02/AC-16 |

R-2 is accepted without argument: the near-duplicate filter was adopted from
CLIN-SUMM one revision earlier and was wrong here. It would have let the N+1
run make zero brief calls whenever the new commit resembled an old one,
silently voiding the incremental proof that is this FR's reason to exist.

R-6's raw read was performed before this fold and changed the frozen brief
schema three times — the `salient_other` cap, `paths_changed_count`, and
multi-reference `why` all exist because reading three real diffs against three
hand-authored briefs showed the schema dropping things that mattered. The
protocol's "one named currency" wording is also corrected: unlike units are
now reported separately.

## Research route outcome

The route did not endorse this FR as first drafted, and the Judge should see
that plainly. Full record: [FR-981.research.md](FR-981.research.md).

| Persona | Class | Verdict |
|---|---|---|
| os-infra-primitivist | subtraction (convergent ×2) | dissent |
| data-process-planner | schema-data (convergent ×2) | dissent |
| yamlgraph-native-planner | schema-data (convergent ×2) | dissent |
| subtractionist | subtraction | pursue |
| librarian | external-method | pursue |

Three findings changed this FR:

1. **The dissenters' premise was false, and they could not know it.** Two
   personas voted to withdraw the pattern documentation on the grounds that
   the only evidence was a single second-hand anecdote. The librarian — run
   in parallel, so invisible to them — found CLIN-SUMM: a medRxiv preprint
   (not peer-reviewed), clinician-evaluated, implementing all four
   properties, whose method was read at the source rather than taken from the
   persona's summary. That is a documented, quantified, independent instance,
   which is enough to refute "single unverifiable anecdote". The withdrawal
   argument is rejected on its premise. Its *principle* survives as the
   pattern doc's separated grading, and as a standing condition: if this FR
   is not enforced, that doc keeps its UNEXERCISED grade permanently.
2. **Four of five rows answer `is_this_a_graph: No`** for the retention half
   — identity and staleness need Python ownership outside the graph. Folded
   answer, now stated in both the doc and § Proposed Solution: *the phases
   are a graph; the store is not.*
3. **"Narrated rather than counted is unfalsifiable"** (both `schema-data`
   rows) is adopted as the load-bearing acceptance criterion, and extended:
   the saving must be reported together with the loss, in one named currency.

## Ideal Result

A newcomer runs one command against any tracked path in this repository and
gets a dossier that reads like a good colleague's briefing: what this module
is for, the three decisions that shaped it, what broke and how it was fixed,
what is still unsettled — every claim traceable in two hops to a commit SHA.
They add a commit, run again, and the run record shows one model call. The
store on disk is plainly derived data: deletable, rebuildable, never the only
copy of anything. Nothing about the demo is specific to git; swapping the
record source for service reports or support tickets changes adapters, not the
graph.

The minimal path back from that: one graph, one brief prompt, one rollup
prompt, a Python store node that owns identity and invalidation, and a run
record that prints the call arithmetic.

## Proposed Solution

**Subject:** exactly one normalized repo-relative tracked path per invocation
(R-3). **Record:** one commit in the frozen selected history window for that
path. **Record identity:** `(path, commit_sha)` — immutable, free, and already
a content hash, satisfying the freeze requirement at zero cost.

```text
START -> enumerate (python: freeze the selected window for one path)
      -> plan_briefs (python: store lookup; emits every missing record)
      -> brief (map: llm, one commit each)  [skipped when nothing is missing]
      -> persist (python: validate + write briefs, stamp versions)
      -> load_briefs (python: read the subject's briefs, date-ordered)
      -> rollup (llm: briefs only)
      -> render (python: dossier + run record) -> END
```

**Enumeration and window (R-3).** `git log --follow` over one path, ordered
deterministically by commit date then SHA. `max_commits` defaults to 30 and
may not exceed 60; when history is longer, the newest window is selected and
the run record discloses `discovered`, `selected`, `omitted_older`, the first
and last selected date, and the first and last selected SHA. Zero commits for
a path is a loud failure, not an empty dossier.

**Ceilings.** Preflight, before the first model call: at most 60 selected
commits, 20 kB diff per brief (truncate, and record the truncation in the
brief envelope), and a planned-call limit of `selected + 1`. For one module
the static maximum is therefore 60 brief calls plus one rollup call — the
first draft's three-module and 200-call ceilings were unexplained and are
removed. A wall-clock limit cannot be enforced before the first call and is
described as a runtime abort, not a preflight ceiling.

Brief shape (inline schema in the prompt YAML), with the three fields the
pilot read forced (see [FR-981-pilot-raw-read.md](evidence/FR-981-pilot-raw-read.md)):

```yaml
brief_schema_version: 1
path: "yamlgraph/utils/llm_factory.py"
commit_sha: "9c6e77a3..."
commit_date: "2026-09-03"
paths_changed_count: 7          # deterministic; the keyhole warning
change_kind: feat | fix | refactor | test | docs | chore
what_changed: "one sentence, mechanism not adjectives, scoped to THIS path"
why: "linked FR/issue references, may be several, or 'not stated'"
salient_other: "<= 600 chars: the non-obvious finding in the commit body"
truncated: false
confidence: high | low
```

Deterministic code owns `path`, `commit_sha`, `commit_date`,
`paths_changed_count`, `truncated`, all counts, and all date ranges. The model
authors the prose fields and `change_kind`. `confidence: low` is the
abstention shape: a merge commit or an empty-diff touch emits a flagged brief.

Three schema decisions come from the pilot read rather than from design: the
`salient_other` cap rose to 600 characters and is explicitly prompted for the
commit body's non-obvious finding, because a 200-character cap dropped both an
inverted latency measurement and an operational 500-on-temperature trap;
`what_changed` is contractually scoped to the subject path because a
path-scoped brief otherwise reports whole-commit claims as this path's change;
and `why` accepts several references because commits bundle FRs.

**Every selected commit produces exactly one brief (R-2, C-3).** The first
draft adopted CLIN-SUMM's Jaccard near-duplicate filter. It is removed and
explicitly not authorized: it breaks the one-to-one record/brief relation,
breaks coverage and provenance, and would let the required N+1 run make zero
brief calls whenever the new commit happened to resemble an old one —
destroying the load-bearing proof. The filter remains a legitimate move in the
pattern at large; it cannot ride in the witness.

**Store (R-4).** `tmp/module-history/briefs/<subject_key>/<sha>.yaml` —
gitignored, derived, rebuildable, never committed. `subject_key` is a
collision-resistant deterministic key combining the normalized repo-relative
path with a hash of it, not a lossy slug. Every stored brief is a
Pydantic-validated envelope carrying collector-owned identity and date, the
model-authored fields, `brief_schema_version`, `prompt_version`, the resolved
provider and model, truncation metadata, and the source path. A malformed or
corrupt envelope fails the run loudly: it is never treated as a cache hit and
never silently discarded. `plan_briefs` re-briefs when
`brief_schema_version`, `prompt_version`, or the resolved provider/model
differs from the current run. Because `commit_sha` is immutable, source-hash
drift cannot occur for this corpus — the demo records that as the reason
invariant 2 is trivially satisfied here and will not be for mutable-record
subjects.

**Rollup output and citations (R-4).** The rollup returns a typed list of
claims, each carrying one or more stored-brief references. Deterministic
render code rejects unknown or missing references and proves every accepted
reference resolves to a brief whose collector-owned commit SHA is present.
Provenance is therefore a test, not a paragraph.

**Incrementality design: regenerate, not cumulative.** CLIN-SUMM's
incremental-update prompt folds each new note into the standing summary,
which is cheaper on long histories but path-dependent — the dossier cannot be
re-derived from the store. This demo regenerates the rollup from all briefs,
accepting one rollup call per read in exchange for idempotence, because the
demo's purpose is to make the arithmetic checkable. The trade-off is recorded
in the pattern doc so a reader with long histories can choose the other way.

**Where the graph boundary falls (research finding 2):** `enumerate`,
`plan_briefs`, `persist`, `load_briefs`, and `render` are Python; only the
`brief` map and the `rollup` call are LLM nodes. The README must say that the
store is deliberately *not* graph state, and cite `book-summary`'s
`all_summaries` add-reducer as the counterexample — per-run state, and the
reason that demo recomputes.

**Cost and loss protocol, frozen before authority (R-6).** The comparison is
two paths over one committed question fixture, not one number. Frozen here:
a small committed question set about the subject module with source-backed
expected answers; a source-path prompt and a brief-path prompt; the tokenizer
and counting method; and a deterministic answer-scoring rule. The witnessed
run reports, separately and without collapsing unlike units: source-input
tokens, brief-input tokens, questions correctly answered on each path, the raw
answers, and every concrete omission observed. No quality threshold is claimed
— the pilot samples do not support one, and inventing a pass bar the evidence
cannot carry is the defect this protocol exists to avoid.

**Authoring route (R-7).** `graph.yaml` and `prompts/*.yaml` are governed
artifacts, authored solely via `scripts/author.sh`, with
`tmp/draft-authoring-report.md` as the verification record. Its task brief is
deliverable D-2 and must be committed at
`feature-requests/authoring-briefs/fr-981-module-history-phased-summary-brief.md`
**before** the first `author.sh` invocation — written then, against the RED
suite, as FR-775's brief was. It is deliberately not pre-written here:
implementation is not authorized, and a brief authored ahead of its failing
tests pins a shape nothing has yet condemned. This FR does not pre-author the
graph either; the sketch above is a design freeze, not a draft.

**Requirement contract (R-7).** The demo adds **no** CAP or REQ identifier. It
exercises existing graph-loading, linting, LLM, map, and Python-node
requirements — including REQ-YG-040 and REQ-YG-041 for map compilation and
reduction — and every new test carries the applicable existing
`@pytest.mark.req` marker. If enforcement discovers that a framework change or
a new capability is genuinely required, it stops and returns to Plan through a
separate FR rather than allocating an ID or widening this one.

## Acceptance Criteria

Superseded by the 2026-09-04 judgement's revised criteria, reproduced here
because the FR is the source of truth for implementation. AC-01 is satisfied
by this revision; the rest activate at enforcement.

- [x] AC-01: R-1..R-7 folded into the committed FR, citing
      [FR-981-pilot-raw-read.md](evidence/FR-981-pilot-raw-read.md) — three pilot
      source-diff/brief pairs with concrete retained and dropped details.
- [ ] AC-02: the FR cites the committed authoring brief, and governed
      graph/prompt artifacts are produced only by `scripts/author.sh`, with
      `tmp/draft-authoring-report.md` naming artifacts, precedent, lint,
      smoke, repairs, and blocked validation.
- [ ] AC-03: `examples/demos/module-history/` contains the frozen graph,
      prompt, Python-tool, README, question-fixture, raw-answer, and
      witnessed-run surfaces.
- [ ] AC-04: `yamlgraph graph lint examples/demos/module-history/graph.yaml`
      passes, and a recorded real-model smoke run over one small frozen
      module window completes with the resolved provider/model recorded.
- [ ] AC-05: enumeration accepts exactly one normalized repo-relative tracked
      path, follows renames, freezes at most 60 date-ordered commits, and
      records discovered, selected, omitted, first/last date and first/last
      SHA before any model call.
- [ ] AC-06: tests prove zero-history rejection, renamed-path identity,
      over-window disclosure, 20 kB per-diff truncation with omission
      metadata, and preflight rejection before any LLM call when an item,
      byte, or planned-call ceiling is exceeded.
- [ ] AC-07: every selected commit produces exactly one validated brief; merge
      and empty-diff touches produce `confidence: low` briefs rather than
      disappearing; no near-duplicate filter exists.
- [ ] AC-08: for N selected commits, the first run records N brief calls, zero
      reused briefs, one rollup call; after one distinct new commit the second
      records one brief call, N reused briefs, one rollup call; an unchanged
      third records zero brief calls, N+1 reused briefs, one rollup call.
      Counts come from deterministic instrumentation at the LLM seams.
- [ ] AC-09: independent tests prove that changing each of
      `brief_schema_version`, `prompt_version`, and the resolved
      provider/model invalidates all applicable cached briefs, while unchanged
      valid envelopes are reused.
- [ ] AC-10: store tests prove collision-resistant subject keys, Pydantic
      validation on write and read, explicit failure on corrupt envelopes, and
      no source diff text in any stored brief or rollup prompt input.
- [ ] AC-11: rollup output is typed as claims with brief references;
      deterministic rendering rejects missing or unknown references and proves
      every rendered claim reaches one or more valid briefs and then
      collector-owned commit SHAs.
- [ ] AC-12: the frozen comparison protocol runs the same committed question
      set through source and brief paths and records tokenizer/method,
      source-input tokens, brief-input tokens, raw answers, deterministic
      correct-answer counts, and concrete omissions — without claiming an
      unevidenced pass threshold.
- [ ] AC-13: the run record prints normalized subject, selected range,
      truncations, planned/actual brief calls, rollup calls, reused briefs,
      invalidated briefs, resolved provider/model, prompt/schema versions, and
      store path; deterministic values are never supplied by the model.
- [ ] AC-14: `reference/patterns/phased-summary.md` is **created** and indexed
      in `reference/README.md`. It labels external shape evidence as
      preprint-grade, names this demo for YAMLGraph composition only after
      AC-04 and AC-08 pass, lists exercised and unexercised invariants, and
      states that the store is derived data outside graph state.
- [ ] AC-15: the README names subject, record, selected-window semantics,
      store location, graph/store boundary, rebuild procedure, cost ceilings,
      and the regenerate-not-cumulative trade-off.
- [ ] AC-16: new tests use applicable existing requirement markers, and
      `python scripts/req_coverage.py --strict` passes with no new CAP/REQ
      allocation and no change under `yamlgraph/`.
- [ ] AC-17: a changelog fragment and a diary entry with a Seed are committed,
      and the FR records implementation status, validation commands, witness
      paths, and deviations.

**Capability question — closed by the judgement.** This is a contrib/example
with pattern documentation, not a framework primitive and not a new
capability. No CAP or REQ identifier is allocated; existing markers including
REQ-YG-040/041 apply.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A | **Extend `corpus_census` (FR-892) with a brief store** and invoke it with git slots. | REJECTED for this FR. Census's contract is coverage arithmetic over a frozen population; adding durable per-item state and an invalidation rule changes that contract and puts the store's failure modes inside a pipeline four FRs depend on. Revisit after the pattern has a witness — then the store may be offered to census, not imposed on it. |
| B | **Extend `book-summary` (FR-775) with a store.** | REJECTED. Its subject is one document and its briefs are pages; grafting a subject axis onto it would obscure the demo it already succeeds at, and its PDF fixture makes the second-run proof slow. |
| C | **Use support tickets or service reports as the demo domain.** | DEFERRED. Better for a non-technical audience and closer to the motivating clinical case, but needs synthetic fixtures — invented data with invented salience, which cannot support the raw-read criterion. Git history is real, free, immutable, and already in the repository. Recommended as the *second* invocation once the machinery is proved. |
| D | **Document the pattern only; ship no demo.** | REJECTED. `gate_checks_shape_not_substance`: a pattern doc whose distinguishing claims are unexercised is a claim, not a pattern. The three untested properties are precisely the ones the doc is for. |
| E | **Withdraw the pattern doc; retire this FR** (research classes 2, two personas, the route's only in-repo `pursue`). | REJECTED on its premise — see § Research route outcome. The principle is kept: the doc grades its two claims separately and must keep the UNEXERCISED grade if this FR dies. |
| F | **Port CLIN-SUMM's design as a clinical demo** (research class 3, librarian). | REJECTED as a witness corpus — the brief's own constraint forbids clinical data, and a synthetic clinical corpus has invented salience. ADOPTED as design input: schema shape, redundancy filter, windowing, and the cumulative-vs-regenerate trade are all folded into § Proposed Solution and the pattern doc. |
| G | **Add a durable brief-store primitive to `yamlgraph/`** (research class 4; where the four `is_this_a_graph: No` rows say retention belongs, if anywhere). | DEFERRED to its own judged scope. The brief fences framework change out, and a primitive built before a single witness exists is `growth_as_default`. |

`is_this_a_graph`: **the phases are; the store is not.** Fan-out over commits
with one model call each plus an LLM reduction fires the FR-853 trigger, and
`yamlgraph graph list` shows no existing graph with a durable per-item store.
But four of five research rows converged on retention requiring Python
ownership outside the graph boundary, and they are right: graph state is
per-run. The first draft of this FR answered a flat "yes" and was wrong.
**[Withdrawn 2026-09-04 — see § Amendment correction 2. A second sole-route
run, pointed at two committed graphs that keep durable keyed stores in YAML,
returned four of five answering "yes". This paragraph's conclusion is
overstated; the question is reopened and owed at enforcement.]**

## Related

- [reference/patterns/phased-summary.md](../reference/patterns/phased-summary.md)
  — the pattern this witnesses.
- [FR-981-module-history-phased-summary-demo.judgement.md](FR-981-module-history-phased-summary-demo.judgement.md)
  — the judgement this revision folds.
- [FR-981-pilot-raw-read.md](evidence/FR-981-pilot-raw-read.md) — the pre-authority raw
  read (R-6): three source/brief pairs and the three schema defects they found.
- [FR-981.research.md](FR-981.research.md) — the route record: five personas,
  six folded classes, the preserved dissent, and the verified external
  precedent.
- [feature-requests/research-briefs/fr981-phased-summary-witness-brief.md](research-briefs/fr981-phased-summary-witness-brief.md)
  — the closed problem brief the route consumed.
- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md)
  — sibling pattern; hierarchical reduce reused when a module's briefs exceed
  one context.
- [examples/demos/book-summary](../examples/demos/book-summary/README.md) —
  the shape this extends.
- [docs/2026-09-02-brainstorm-business-use-cases.md](../docs/2026-09-02-brainstorm-business-use-cases.md)
  — §3 names cross-product and temporal census as new shapes; subject-scoped
  phased summary is a third, and N6/N9 are candidate consumers.
