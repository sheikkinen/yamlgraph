# Feature Request: Module-History Demo — YAMLGraph Witness for the Phased Summary Pattern

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed — revised 2026-09-04 after the research route dissented
against the first draft (§ Research route outcome)
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
witnesses, and
[`reference/patterns/phased-summary.md`](../reference/patterns/phased-summary.md)
now grades those two claims separately for exactly this reason.

## Value Statement

A developer evaluating YAMLGraph sees a pattern documented with one external
anecdote; after this FR they can run it, read the store on disk, add a commit,
and watch the incremental cost be one call. The repository gets the same thing
it gives the reader: a module dossier that is cheaper to keep current than to
regenerate.

## Problem

1. **The composition has no runnable witness.** `phased-summary.md` documents
   invariants that nothing in this repository exercises. The shape is
   externally proven — that part of the first draft's problem statement was
   wrong and the research route corrected it — but a reader of a YAMLGraph
   pattern document is asking whether it composes *here*, and no committed
   graph answers that. `demo_vs_test`: demos prove the abstraction is worth
   having.
2. **The distinguishing properties are the untested ones.** Map-plus-reduce is
   precedented five times over. The store, the invalidation rule, and the
   incremental call count are precedented zero times — which is exactly why
   the demo must assert them mechanically rather than narrate them in a
   README.
3. **The repository has the problem the pattern solves.** Onboarding onto a
   module means reading its history; `git log` returns transport fragments,
   and asking a model to read 200 diffs is the
   `impossibly_large_sequential_task` framing with no store to amortise it.

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
- **R-3 (re-enter judgement from the committed revision) — DONE**, this
  record's second execution.

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

**Subject:** a tracked file path. **Record:** one commit touching it.
**Record identity:** `(path, commit_sha)` — immutable, free, and already a
content hash, satisfying the freeze requirement at zero cost.

```text
START -> enumerate (python: git log --follow -- <path>, capped)
      -> plan_briefs (python: store lookup; emits only the missing records)
      -> brief (map: llm, one commit each)  [skipped when nothing is missing]
      -> persist (python: write briefs, stamp versions)
      -> load_briefs (python: read the subject's briefs, date-ordered)
      -> rollup (llm: briefs only)
      -> render (python: dossier + run record) -> END
```

Brief shape (inline schema in the prompt YAML):

```yaml
brief_schema_version: 1
path: "yamlgraph/utils/llm_factory.py"
commit_sha: "9c6e77a3..."
commit_date: "2026-09-03"
change_kind: feat | fix | refactor | test | docs | chore
what_changed: "one sentence, mechanism not adjectives"
why: "linked FR/issue, or 'not stated'"
salient_other: "<= 200 chars, or empty"
confidence: high | low
```

Deterministic code owns `path`, `commit_sha`, `commit_date`, all counts, and
all date ranges. The model authors only the three prose fields and
`change_kind`. `confidence: low` is the abstention shape: a merge commit or an
empty-diff touch emits a flagged brief, never a confident blank one.

**Store:** `tmp/module-history/briefs/<path-slug>/<sha>.yaml` — gitignored,
derived, rebuildable. `plan_briefs` treats a brief as stale when
`brief_schema_version`, `prompt_version`, or `model` differs from the current
run, and re-briefs it. Because `commit_sha` is immutable, source-hash drift
cannot occur for this corpus — the demo records that as the reason invariant 2
is satisfied trivially here and will not be for mutable-record subjects.

**Near-duplicate filter (adopted from CLIN-SUMM):** `plan_briefs` drops a
commit whose diff is near-identical to one already briefed for that path,
using a deterministic string similarity, before any model call. Git has fewer
copy-forward duplicates than clinical notes, so this will fire rarely here —
it is included because a cheap comparison that removes a model call is the
best trade in the pattern, and a witness that omits it teaches the pattern
wrong.

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

**Ceilings, enforced before the first model call:** 60 commits per module, 3
modules per run, 20 kB diff per brief (truncate and record the omission), 200
total calls, 10-minute wall clock.

**Authoring route:** `graph.yaml` and `prompts/*.yaml` are governed artifacts —
authored solely via `scripts/author.sh` per the graph-authoring doctrine, with
the `tmp/draft-authoring-report.md` artifact as the verification record. This
FR does not pre-author them; the sketch above is a brief, not a draft.

## Acceptance Criteria

- [ ] `examples/demos/module-history/` exists with `graph.yaml`, prompts,
      `tools.py`, and a README naming the subject, record, and store location.
- [ ] `yamlgraph graph lint` passes; a smoke run over one capped module
      completes on the default small model.
- [ ] **Incremental proof (the load-bearing criterion):** a test runs the
      graph over N commits, then over N+1, and asserts the second run makes
      exactly one brief call and reuses N briefs. Model calls are stubbed; the
      arithmetic is real.
- [ ] **Invalidation proof:** bumping `prompt_version` re-briefs all N; a test
      asserts it.
- [ ] **Isolation proof:** a test asserts no source diff text reaches the
      rollup prompt input (invariant 4) — the rollup sees briefs only.
- [ ] **Provenance proof:** a test asserts every rendered dossier claim carries
      a brief reference, and every brief a commit SHA (invariant 5).
- [ ] **Cost-currency proof (research finding 3):** the witnessed run reports
      the saving *and* the loss in one named currency — tokens read via the
      brief-routed path versus the direct-source path for the same fixed
      question set, alongside how many of those questions the brief-routed
      path answers wrongly or not at all. A saving quoted alone does not
      satisfy this criterion; CLIN-SUMM's 69.86% saving beside 4.65/5
      completeness is the reporting shape to match.
- [ ] The run record prints planned vs. actual brief calls, reused briefs, and
      the store path; a run that exceeds a ceiling fails before the first call.
- [ ] `reference/patterns/phased-summary.md` has its *YAMLGraph composition*
      grade moved off UNEXERCISED to name this demo, listing which invariants
      it actually exercises and which remain untested here. The *shape* grade
      does not change — it never depended on this FR.
- [ ] The demo README states that the store is not graph state, and why.
- [ ] A witnessed real-model run is recorded (log committed under the demo,
      book-summary style) — including one raw read: three commits read against
      their briefs, with the concrete detail each brief dropped.
- [ ] Changelog fragment in `changelog/unreleased/`.
- [ ] Diary entry with a Seed.

**Open for the Judge:** whether this demo claims a new capability. If it does,
the CAP/REQ IDs must come from the FR-975/FR-980 reservation route; no ID is
allocated in this draft. If it does not, tests tag existing map/loop REQ IDs.

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

## Related

- [reference/patterns/phased-summary.md](../reference/patterns/phased-summary.md)
  — the pattern this witnesses.
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
