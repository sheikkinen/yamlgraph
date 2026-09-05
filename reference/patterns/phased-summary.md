# Phased Summary Pattern

Compress each long record about one subject into a short typed **brief**, store
the briefs durably, and build the subject's **rollup** from briefs alone. The
brief — not the source record — is what every downstream reader consumes.

The topology is:

```text
record -> typed brief -> brief store (entity-keyed, date-ordered)
       -> rollup (LLM over briefs only) -> dossier
```

This is an architecture pattern above the [`map` node](../map-nodes.md)
contract. It shares its fan-out with
[Corpus Map-Reduce](corpus-map-reduce.md) and its compression move with the
[Compaction Pattern](../compaction-pattern.md), but it answers a different
question: not *"did we read all N?"* and not *"is the running context small
enough?"* — rather *"what does a new reader need to know about this subject,
and what does it cost to keep that current?"*

> **Evidence base — two claims, graded separately.**
>
> *The shape: PROVEN, and independently reinvented.* An operator-reported
> production pipeline reduces each clinical visit note to a fixed-shape
> brief and builds the patient summary from the briefs. CLIN-SUMM
> ([medRxiv](https://www.medrxiv.org/content/10.64898/2025.11.28.25341233v3.full))
> arrived at the same construction independently, and measured it. Note the
> grade of that evidence: CLIN-SUMM is a medRxiv **preprint**, so it is a
> documented and quantified instance, not a peer-reviewed result.
> Its organising ancestor is sixty years older: Weed's problem-oriented
> medical record (1964; NEJM 1968). Two independent arrivals on one
> construction, over the same corpus, is evidence the shape is forced by
> the problem rather than chosen.
>
> *The YAMLGraph composition: PARTLY EXERCISED.* The **store and the
> integrity gate** are committed and working — see
> [`wiki-memory`](../../examples/demos/wiki-memory/README.md) (CAP-173,
> CAP-174) and [`novel_fandom`](../../examples/novel_fandom/README.md)
> (CAP-181), which keep typed keyed artifacts across runs and refuse model
> output that would corrupt them. What is **unexercised** is the rest:
> substitution (a brief standing in for its source in later prompts), the
> subject-scoped rollup, version-keyed invalidation, and the counted
> incremental cost. The nearest whole-shape precedent,
> [`book-summary`](../../examples/demos/book-summary/README.md) (FR-775), has
> the two phases but discards its briefs, has no subject axis, and recomputes
> on a second run. FR-981 proposes the witness for what remains.
>
> This grade is a correction. The first draft read UNEXERCISED with "nothing
> committed in this repository runs it", because every search behind it was
> keyed on the vocabulary of summarisation and the two witnesses share the
> problem while sharing no word.

## What distinguishes it

| Property | Phased summary | Corpus map-reduce | Compaction |
|---|---|---|---|
| Per-item output | **Durable; substitutes for the source** | Finding; source stays primary | Transient working state |
| Grouping | **By subject, ordered in time** | By partition, order incidental | Single session |
| Second run | **One new brief + one rollup** | Full re-census | Continuous within a run |
| Reduce | **LLM, and it is the product** | Optional; prefer deterministic | LLM, to shrink state |
| Question answered | "Who is this subject?" | "Did we read all N?" | "Does this still fit?" |

Four properties define the pattern, and all four must hold:

1. **The brief is durable and substitutive.** Written once per record, it
   thereafter replaces the source note in every downstream prompt.
2. **Briefs are subject-scoped and chronologically ordered.** The rollup is a
   longitudinal narrative, not a theme reduction.
3. **The store makes it incremental.** Record n+1 costs one brief and one
   rollup, not n+1 briefs. This is the whole reason the phases are separate.
4. **The brief is a fixed shape, closer to extraction than to prose.**
   `date, keuhkokuume, penisilliini, 7 päivää` composes; a paragraph of free
   prose per record does not.

Drop property 1 or 3 and this is book-summary. Drop property 2 and it is a
census. Drop property 4 and the rollup inherits an unbounded, unqueryable
input and the pattern buys nothing.

## Prior art outside this repository

This pattern is not an invention of this project. Read the precedent before
designing a brief schema — it has already answered questions this document
would otherwise leave to trial.

**CLIN-SUMM** (Clinical Longitudinal Insight from Notes using Summarization,
[medRxiv](https://www.medrxiv.org/content/10.64898/2025.11.28.25341233v3.full)),
consolidating multi-visit EHR narratives:

- **Brief shape:** seven fixed sections — chief complaints, history of present
  illness, past medical history, medications and allergies, vitals/labs,
  diagnosis, treatment plan — plus an eighth, *Changes over Time*, present only
  from the second encounter onward. Every entry date-stamped.
- **Store:** a structured Parquet file with metadata linking patient, note
  date, and summary; computed once and, in the authors' words, reused across
  downstream tasks rather than reprocessing raw notes. Property 1, exactly.
- **Two prompts, not one:** an initial prompt organises the first note into the
  seven sections; an incremental-update prompt reads the *prior summaries* and
  adds only novel information, plus the *Changes over Time* delta.
- **Redundancy filter:** a Jaccard similarity filter skips near-identical
  notes before any model call — a cheap deterministic gate this document had
  not considered, and an obvious one in any corpus with copy-forward records.
- **Windowing:** a 50-summary sliding window bounds context on long histories.
- **Measured, not asserted:** 69.86% space savings across the cohort (3.6B to
  1.1B tokens); 52.6 ± 31.2% at patient level; clinician-rated correctness
  4.69/5 and completeness 4.65/5 with under 4% hallucination; $250 per 100
  dementia patients on a frontier model versus $35 on an open one.

**POMR** (Weed, first published 1964; NEJM 1968) is the paper ancestor and
the reason the clinical framing feels natural: observations, assessments, and
plans are grouped **by problem** rather than by date, with SOAP-structured
progress notes attaching to problems. Its Problem List is a durable
substitutive artifact maintained by hand — the same move, sixty years before
the model.

The convergence matters more than either instance. An operator's production
system and a documented framework arrived at the same construction
independently over the same kind of corpus, and both landed on a fixed
per-record schema, retention, and a subject-scoped rollup. That is the
signature of a shape forced by the problem.

## Where the graph boundary falls

The fan-out and both LLM calls are ordinary graph work. The interesting
question is the store, and this document's first draft answered it wrongly —
worth recording, because the wrong answer is the intuitive one.

That draft reasoned: graph state is per-run and ephemeral, `book-summary`'s
`all_summaries` add-reducer is exactly that and is why that demo recomputes,
therefore retention must be Python owned outside the graph. A five-persona
research route agreed four-to-one.

Two committed graphs disagree, and they are evidence rather than reasoning:

- [`examples/demos/wiki-memory`](../../examples/demos/wiki-memory/README.md)
  writes one typed file per key with `write_data_file`, reads the accumulated
  set back on a later run through a `data_files` glob, and gates persistence
  with a `type: python` node — all declared in YAML.
- [`examples/novel_fandom`](../../examples/novel_fandom/README.md) keeps a
  typed, entity-keyed canon the same way, under a no-orphan-reference gate and
  a lane-immutability rule.

A second research run pointed at those witnesses returned four of five the
other way. So: **the store is expressible in a graph**, using
`write_data_file` for the write, a `data_files` glob for the read-back, and
Python *nodes* — inside the graph, not beside it — for identity and
integrity. Prefer that composition over hand-rolled persistence.

What remains genuinely outside the declarative surface is narrower than the
first draft claimed: the *policy* of staleness — deciding that a brief whose
`prompt_version` or model has changed must be rebuilt — is code, wherever you
put it. The mechanism is not.

The general lesson outlives this pattern: reasoning about what a framework
*can* express loses to reading what it already expresses.

## When to use

Use it when all of these hold:

1. The subject accumulates many records over a long period.
2. Any single record is far longer than what a future reader needs from it.
3. A new reader must be oriented quickly, without reading the archive.
4. New records arrive continuously, so full recomputation is the wrong price.
5. The questions the rollup must answer are known in advance, so the brief
   schema can be designed against them.

Typical subjects: a patient, a machine under service, a customer account, a
legal or claims case, a supplier, a property, a contributor, a source module.

Do not use it when:

- the corpus has no subject axis — that is
  [Corpus Map-Reduce](corpus-map-reduce.md);
- completeness proof is the deliverable, not orientation — same;
- the records interact and cannot be judged independently (a later record
  changes what an earlier one *meant*) — the brief boundary is wrong;
- the reader needs the full record anyway, in which case a brief is an extra
  hop and a lossy one;
- the questions are open-ended and unpredictable, so no brief schema can be
  designed — retrieval over sources fits better than substitution.

## The three stages

### 1. Brief

One record in, one typed brief out, one narrow judgement. Use a cheap model:
the task is bounded extraction with light summarisation, and the input is one
record, not a corpus.

```yaml
brief_schema_version: 2
entity_id: "patient-4417"
record_id: "visit-2026-03-11-a91c"
record_sha256: "..."
record_date: "2026-03-11"
condition: "keuhkokuume"
intervention: "penisilliini"
duration: "7 vrk"
salient_other: "penicillin tolerance confirmed; no prior reaction"
confidence: high
model: "claude-haiku-4-5"
prompt_version: 3
```

Rules:

- The schema is the design decision of the entire pattern. Everything it
  omits becomes invisible to every future reader.
- The brief carries subject identity, record identity, and record date — all
  three supplied by deterministic code, never authored by the model.
- Give the model an explicit way to abstain. A record it cannot compress
  emits a flagged exception brief, not a confident blank one. An empty brief
  that reads like a normal one is the `plausible_wrong_answer` trap with a
  long half-life.
- Cap `salient_other` in length so an unmodelled fact has somewhere to go
  without the brief drifting back into free prose.
- Filter near-duplicate records deterministically *before* the model call.
  Corpora with copy-forward records — clinical notes, ticket threads, service
  reports — repeat themselves heavily; CLIN-SUMM uses a Jaccard similarity
  filter for this. A cheap string comparison removing a model call is the best
  trade in the pattern.

### 2. Store

The store is what separates this pattern from a two-node pipeline. In
YAMLGraph, build it from `write_data_file` and a `data_files` glob rather than
hand-rolled persistence — `wiki-memory` and `novel_fandom` are the working
precedents.

- Key each brief by **immutable record identity** plus content hash.
- Group by subject; sort by record date.
- Stamp every brief with `brief_schema_version`, `prompt_version`, and
  `model`.
- Invalidate a brief when its source hash changes, when the schema version is
  bumped, or when the prompt or model that produced it changes. Invalidated
  briefs are regenerated, never patched.
- A brief is derived data. It may be deleted and rebuilt at any time; nothing
  downstream may hold the only copy of a fact.

### 3. Rollup

One LLM call reads the subject's briefs — ordered, briefs only — and emits the
dossier.

- No node may pass a source record into the rollup prompt. If the rollup needs
  something the briefs lack, fix the brief schema and re-run; do not widen the
  rollup's input.
- Every rollup claim cites the brief that supports it; every brief cites its
  source record. Two hops, always resolvable.
- Counts, date ranges, intervals, and totals are computed in code over the
  store and injected. No model emits a date.
- The rollup is regenerated, never hand-edited. An edited rollup is a fact
  with no source.
- When a subject's briefs exceed one context, insert period rollups (per year,
  per phase) and roll those up. The hierarchical reduce from
  [Corpus Map-Reduce](corpus-map-reduce.md#5-reduce-optional) applies here
  unchanged. CLIN-SUMM's sliding window over the most recent 50 summaries is
  the cheaper variant when recency dominates and old detail may fade.

#### Two ways to organise the rollup

A dossier can be ordered by **problem** — one section per condition, fault,
account issue, or open thread, each carrying its own history — or by
**chronology**, one entry per period. POMR chose problem; a naive timeline
chooses chronology; CLIN-SUMM does both, sectioning by clinical domain with
date stamps inside each section, so a reader can enter by problem and still
see when.

Pick deliberately, because the two answer different questions: *"what is going
on with this subject"* versus *"what happened, in order"*. The choice is
independent of the brief schema — which is the point of retaining briefs.

**Both organisations draw provenance from the same brief store.** This is what
the retained brief buys beyond speed: whichever way the dossier is cut, every
claim in it resolves to the brief that carries it, and every brief to a dated
source record. A rollup written directly from sources can be cut either way
too, but nothing underneath it can be re-cut, re-checked, or re-derived
without spending the whole corpus again.

#### Two ways to be incremental

| | Regenerate from briefs | Cumulative update (CLIN-SUMM) |
|---|---|---|
| New record costs | 1 brief + 1 rollup | 1 brief + 1 update |
| Rollup input | all briefs, every time | prior summary + new brief |
| Reproducible | yes — idempotent from the store | no — path-dependent |
| Drift | none | compounds across updates |
| Best when | the dossier must be auditable | histories are long and read often |

CLIN-SUMM's incremental-update prompt reads the previous summaries and adds
only novel information. That is cheaper on long histories and inherently
chronological — it never sees the future. It also means the dossier cannot be
re-derived from the store alone, so an error introduced at encounter 40
persists and cannot be diffed away. Prefer regeneration when the dossier is
evidence; prefer cumulative update when it is a reading aid.

## Required invariants

1. Every in-scope record has exactly one current brief, or a recorded
   exception.
2. Brief identity is source identity; a changed source invalidates its brief.
3. Every brief records the schema version, prompt version, and model that
   produced it.
4. The rollup reads briefs only.
5. Every rollup claim resolves to a brief, and every brief to a source record.
6. Counts, dates, and totals in the rollup are computed in code, not stated by
   the model.
7. Incremental cost is proved, not asserted: a run that adds one record makes
   one brief call plus the rollup calls, and the run record shows it.

## The substitution risk

This is the pattern's one serious hazard and it deserves its own budget.

The brief is lossy **and** durable. Whatever the schema omits disappears from
every future reader's view, silently — the rollup will still read fluent and
complete, because fluency survives the omission. A census that misses an item
leaves a hole in the coverage arithmetic; a brief that drops a fact leaves no
trace at all.

Substitution is a claim, not a property. Compression ratio is not read-cost
saving unless the brief genuinely answers the question the source would have
answered. Fix a cost currency — tokens, money, or reader time — and compare
the brief-routed path against the direct-source path *for the same question*.
CLIN-SUMM does exactly this and reports both halves: 69.86% space saving on
one side, clinician-rated completeness 4.65/5 and under 4% hallucination on
the other. A saving quoted without the completeness number is half a result.

Mitigations, in order of value:

- Enumerate the questions the rollup must answer *before* writing the brief
  schema; design the schema against that list and record the list next to it.
- Measure both halves. Name the currency, measure the saving, and measure what
  the brief-routed path gets wrong on a question set the source can answer.
- Sample and read raw: periodically take N source records and read them
  against their briefs (`read_raw_output_first`). This is the only check that
  finds a systematically silent omission.
- Treat schema changes as re-runs, not migrations. A store holding two schema
  versions answers questions differently for different periods.
- Keep the source records addressable forever. The brief is a fast path, not
  an archive.

## Cost contract

```text
initial      = N brief calls + ceil(N / batch) rollup calls
incremental  = 1 brief call + rollup calls for that subject only
schema bump  = N brief calls again, for every affected subject
```

The third line is the price of the durable store and must be budgeted, not
discovered. Set ceilings for records per subject, brief input size, rollup
batch size, and total calls per run, and enforce them before the first model
call.

## Privacy and egress boundary

Both phases cross the model boundary: sources at brief time, briefs at rollup
time. A brief inherits the data class of its source — a brief of a patient
note is still patient data, and a compact one is not a de-identified one.
Classify at the store, apply the provider policy to both stages, and do
minimisation **in the brief schema**, where it is declared and reviewable,
rather than in a filter after fan-out.

## Operational checklist

Before running:

- [ ] Name the subject, the record, and the immutable record identity.
- [ ] Write down the questions the rollup must answer.
- [ ] Design the brief schema against that list; define the abstention shape.
- [ ] Decide where the store lives and how invalidation is detected.
- [ ] Choose the rollup's organisation: by problem, by chronology, or both.
- [ ] Choose the incremental design: regenerate from briefs, or cumulative
      update — and accept its reproducibility consequence.
- [ ] Add a deterministic near-duplicate filter ahead of the brief call.
- [ ] Set per-subject and per-run ceilings.
- [ ] Choose a provider approved for the data class — for both stages.

After running:

- [ ] Verify the seven invariants.
- [ ] Read raw: N sources against their briefs.
- [ ] Re-run with one added record and confirm the incremental call count.
- [ ] Confirm every rollup claim resolves two hops back to a source.
- [ ] Report the saving and the loss together, in one named currency.

## Precedents

External:

- **CLIN-SUMM**, incremental longitudinal summarization of clinical notes —
  [medRxiv](https://www.medrxiv.org/content/10.64898/2025.11.28.25341233v3.full).
  All four properties, measured. Read this before designing a brief schema.
- **POMR**, Weed 1964 / NEJM 1968 — the problem list and SOAP; the durable
  substitutive artifact before there was a model to build it.

In this repository:

- [`examples/demos/wiki-memory`](../../examples/demos/wiki-memory/README.md)
  (CAP-173, CAP-174) — the store and the integrity gate, in YAML: one typed
  file per key, `data_files` read-back on later runs, a Python gate node
  refusing unresolvable references. Read this before designing a store.
- [`examples/novel_fandom`](../../examples/novel_fandom/README.md) (CAP-181)
  — the same, entity-keyed and typed, plus lane immutability: an authority
  rule protecting stored artifacts from the model.
- [Durable keyed artifact store research](../../docs/2026-09-04-research-durable-keyed-artifact-store.md)
  — the route record behind this section's correction; the store shape is a
  candidate pattern in its own right, and this pattern is its specialisation.
- [FR-775 Book-Summary Loop Redesign](../../feature-requests/FR-775-book-summary-loop-redesign.md)
  — per-unit brief plus LLM reduction; no store, no subject axis.
- [FR-616 Compaction Pattern](../compaction-pattern.md) — the same compression
  move, scoped to one running graph.
- [Corpus Map-Reduce](corpus-map-reduce.md) — the sibling pattern for
  population-scale questions.
- FR-981 — module-history demo; the proposed second witness for this pattern.
