# Problem brief: a documented summarisation pattern whose distinguishing claims nothing in this repository exercises

**Prior art:** FR-775
(`feature-requests/FR-775-book-summary-loop-redesign.md`, Enforced
2026-08-05) built `examples/demos/book-summary`: one LLM call per page,
then one LLM reduction over the ordered page summaries. It is the
closest running shape, and its own prior-art note already recorded that
loops, map fan-out and LLM reduction were each well precedented — the
gap it claimed was the *combination*. FR-774
(`feature-requests/FR-774-book-summary-scale-hardening.md`) is its
superseded predecessor and owns the splitter mechanics. FR-616
(`reference/compaction-pattern.md`) compresses accumulated state inside
one running graph with guard-plus-LLM, discarding nothing to disk.
FR-892 (`feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`)
plus FR-895's synthesize tail is the shared census pipeline: slot-bound
discovery and extraction, deterministic coverage reconciliation, and a
corpus-level brief with a citation boundary. FR-962
(`feature-requests/FR-962-person-profile-census-authored-prs.md`,
Approved with Revisions 2026-09-02) is the nearest subject-scoped run:
unit = authored PR, reduce target = one person, over a date window.
FR-254 (`examples/demos/diary_index/README.md`) maps over a file corpus
into a deterministic Python aggregate with no LLM reduction. A REJECTED-FR
sweep found no prior proposal for a durable per-record summary store.
`prior_art.py` run against this brief's FR returned no hits — retrieval
was silent (FR-938), so this list is a manual floor, not a ceiling.

## Problem statement

An operator reports a production pipeline, outside this repository and
not independently verifiable here, with this shape: each lengthy
clinical visit note is reduced to a short fixed-shape brief (`date,
diagnosis, drug, duration`), the briefs are retained, and the patient's
lifetime summary is built from the briefs rather than from the notes.
A manual sweep of `reference/patterns/`, `reference/*.md` and
`examples/demos/` on 2026-09-04 found no document naming that shape and
no graph running it.

Four properties distinguish it from what this repository already
documents: the per-record output is durable and *substitutes* for the
source in every later prompt; records are grouped by subject and ordered
in time; a new record costs one per-record call rather than a full
recomputation; and the per-record output is a fixed schema rather than
prose. Each of the three neighbouring precedents misses at least two of
the four. `book-summary` holds its page summaries in graph state for the
duration of one run (`all_summaries` add-reducer, per-window `accumulate`
filter) and has no subject axis, so a second run over the same book pays
full price. `corpus_census` retains no per-item artifact and its brief is
corpus-level, not subject-level. Compaction's summary is working state,
alive only while the graph runs. FR-962 is subject-scoped but single-shot:
the next date window re-reads every PR.

The consequence is a documentation claim without an executable witness.
A pattern document in this repository carries an evidence-base line, and
the three claims that would make this pattern distinct — the durable
substitutive artifact, the subject axis, the incremental cost — are
precisely the three that no committed graph, test, or demo exercises.
The properties are also the ones with the sharpest failure modes: a
retained lossy summary makes every omission permanent and silent to all
later readers, and an incremental-cost claim that is narrated rather
than counted is unfalsifiable.

The open question is what, if anything, should carry those three claims
in this repository, and whether they belong in an example, in framework
code, in a test harness, or nowhere at all until a second independent
instance appears.

## Classification

judgement/analysis/generation

## Constraints

- Reference documentation in this repository states an evidence base;
  whatever ships must leave that line true. A claim exercised nowhere
  must be marked as such or withdrawn (`gate_checks_shape_not_substance`).
- Any `graph.yaml` or `prompts/*.yaml` artifact is governed and may be
  authored only through `scripts/author.sh` (FR-767 sole route); no
  manual or delegated authoring.
- A witness must run on the default small model. FR-775's operator
  verdict on its predecessor — "it requires a bigger model and falls
  short to demonstrate yamlgraph" — is the standing bar.
- Retained per-record summaries are derived data. Nothing may become the
  only copy of a fact, and committing derived summaries to the repository
  needs explicit justification.
- The motivating corpus is clinical and may not be used. Any witness
  corpus must be one whose data class permits the configured provider,
  and both phases cross the model boundary, not only the first.
- An incremental-cost claim must be established by counting calls in a
  test, not asserted in a README. A claim about a lossy retained summary
  must be checked by reading raw sources against their summaries
  (`read_raw_output_first`), not by a shape check alone.
- No framework change to `yamlgraph/` rides along on a documentation or
  example scope; if the research concludes that framework code is the
  right home, that is a separate judged scope with its own witnesses.
- New CAP or REQ identifiers must come from the FR-975/FR-980
  reservation route; none may be invented.
- Effort must stay proportionate to a single pattern witness; the
  research must say plainly if the honest disposition is to withdraw or
  downgrade the documentation instead of building anything.
- `is_this_a_graph`: must be answered — whether retention and reuse of
  per-record summaries is expressible as a graph at all, or whether the
  retention boundary is necessarily Python owning identity and staleness
  outside the graph.

## Witnessed incidents

- 2026-09-04, this repository, manual sweep: `grep` over
  `reference/patterns/*.md`, `reference/patterns.md` (14 numbered
  patterns), `reference/compaction-pattern.md` and `examples/demos/`
  returned no document or graph naming a retained per-record summary
  that substitutes for its source. The index at `reference/README.md`
  lists six pattern documents; none carries the subject axis.
- 2026-08-05, FR-775 Enforced: `examples/demos/book-summary/README.md`
  documents `accumulate` selecting only summaries inside the current
  `batch_start..batch_end` window and an `add` reducer appending them to
  `all_summaries` — per-run graph state. The demo's finite budget is 100
  iterations times 10 pages; re-running over the same PDF re-summarises
  every page.
- 2026-09-02, FR-962 Approved with Revisions: unit = authored PR, reduce
  target = one person, scoped to a date window since 2026-06-01. The
  ledger row model and the mechanical rollup are per-run; no PR summary
  survives the run for the next window to reuse.
- FR-892 / FR-895, `examples/demos/corpus_census/README.md`: the
  synthesize tail takes `brief_path` and `brief_rubric` and emits one
  corpus-level brief from the top-N ledger rows under a citation
  boundary — a summary *of the population*, with no per-item artifact
  retained after the run.
- FR-616, `reference/compaction-pattern.md`: guard-plus-LLM compression
  of `history` back into `history`, fired by a token threshold inside a
  running loop. The compressed form is working state and is never keyed,
  stored, or reused across runs.
- Operator report, 2026-09-04, production system outside this
  repository: per-visit briefs of the form `date, keuhkokuume,
  penisilliini, 7 päivää` are retained and a patient-level summary is
  constructed from them. Single instance, second-hand, with no artifact
  available for inspection here — it establishes that the shape is in
  use somewhere, and nothing more.
- 2026-09-04, `prior_art.py` executed against
  `feature-requests/FR-981-module-history-phased-summary-demo.md`:
  exit 0, no hits printed. Filename-noun IDF retrieval found nothing,
  which under FR-938 means the search was silent, not that precedent is
  absent.
