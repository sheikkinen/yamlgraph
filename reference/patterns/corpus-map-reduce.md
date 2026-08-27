# Corpus Map-Reduce Pattern

Analyze every item in a finite corpus with bounded LLM calls, preserve one
primary finding per input unit, and prove mechanically that nothing was
silently omitted.

The topology is:

```text
freeze corpus -> partition -> typed map -> reconcile -> optional reduce -> render
```

This is an architecture pattern above the [`map` node](../map-nodes.md)
contract. It combines [parallel fan-out](../patterns.md#pattern-8-parallel-fan-out-map)
and [pre-chunking](../patterns.md#pattern-10-batched-map-processing) with
provenance, cost bounds, and deterministic coverage reconciliation.

> **Evidence base: PROVEN (multiple instances).** The pattern appears in the
> prompt-theme analyzer (FR-402), FR Atlas (FR-748), requirement-witness audit
> (FR-851), session-shapes classifier (FR-884), reusable corpus-census graph
> (FR-892), and the full-diary reading
> recorded in [The Questioner and the Trace](../../docs/the-questioner-and-the-trace.md).

## When to use

Use this pattern when all of these conditions hold:

1. The input is a finite, enumerable corpus.
2. Each item or bounded partition needs an independent semantic judgement.
3. Completeness matters: "all N read" is part of the result.
4. A cheap structured-output model can make the primary judgement.
5. Counts, identities, and coverage can be checked deterministically.

Typical tasks:

- summarize every pull request in a release window;
- read every commit when no pull-request grouping exists;
- audit every requirement witness or feature request;
- classify a large prompt, diary, test, or document corpus;
- ask one semantic question over every file when keyword search is too narrow
  and retrieval recall cannot be allowed to fail silently.

Do not use it for:

- a single lookup that `git`, `rg`, or a generated index can answer;
- an unbounded stream with no stable snapshot;
- a corpus whose data policy forbids the selected model provider;
- live pull-request merge approval (use the independent review route);
- running one complete graph independently per file, which is the separate
  [Batch-Runner Pattern](batch-runner.md).

## The six stages

### 1. Freeze

Corpus-specific discovery and extraction adapters enumerate the population and
fetch each item. A deterministic collector then freezes the population before
the first model call. It owns input identity and records enough provenance to
replay or audit the run. FR-892's invocation-bound `discover` and `extract`
tool slots are the executable precedent: a new corpus supplies adapters, not a
new graph.

For files, record at least:

```yaml
path: docs/example.md
sha256: "..."
bytes: 4812
```

For GitHub history, use immutable identities:

```yaml
kind: pull_request
number: 123
base_sha: "..."
head_sha: "..."
```

A branch name, mutable tag, issue search result, or "latest" query is not a
frozen identity. Store the resolved IDs and the query/window that produced
them. Deduplicate forked or repeated records before cost accounting.

The collector must reject the run before spending when the population exceeds
declared item, byte/token, or call ceilings.

### 2. Partition

Partition by a declared character or estimated-token budget, not only by file
count. Ten short files and one generated report do not carry equal context
cost.

Each partition retains collector-owned metadata:

- partition ID;
- source item IDs;
- source paths or GitHub URLs;
- byte/character spans for split items;
- total input size;
- stable ordering key.

Split oversized records at semantic boundaries when possible (heading,
paragraph, diff hunk), but retain exact spans so deterministic code can prove
that every source byte belongs to one partition.

Partition sizing controls three risks at once:

- provider context limits;
- rate limits and concurrent fan-out;
- prompt overload that turns one judgement into several unrelated jobs.

### 3. Typed map

Map one narrow judgement over each item or partition. The model returns a
schema, not prose whose IDs and verdicts must be recovered with string
matching.

Example primary result shape:

```yaml
partition_id: p017
items:
  - source_id: pr-123
    summary: "Adds bounded corpus partitioning and coverage reconciliation."
    affected_surfaces: [reference]
    evidence: ["pull/123/files#reference/patterns/corpus-map-reduce.md"]
    uncertainty: "None"
```

The prompt may repeat collector-owned IDs for attribution, but those IDs remain
claims until the reducer checks them. Use a pinned cheap model when the task is
narrow and structured. Demonstrated choices include
`inception/mercury-2` and `anthropic/claude-haiku-4-5`; they are examples, not
universal defaults.

Map errors must fail the overall run. They may fail directly, or a map may use
`on_error: skip` only when deterministic reconciliation rejects map-error rows
and missing source indices. FR-892 uses that second design: skip keeps fan-out
running, while the reducer still makes incompleteness fatal.

### 4. Reconcile

Deterministic code reconciles every model output against the frozen manifest.
This is the trust boundary: the model authors meaning; code authors identity,
coverage, and arithmetic.

The reconciler rejects:

- unknown or fabricated source IDs;
- duplicate results for one source ID;
- missing source IDs;
- malformed or out-of-corpus evidence references;
- a result attached to the wrong partition;
- model-supplied totals that disagree with the manifest.

It computes:

- input items and bytes/spans;
- primary partitions;
- typed map results;
- missing, duplicate, and unknown identities;
- reduction batches;
- actual model-call count;
- corpus and artifact hashes.

Treat every model output as a claim. The more specialized
[Coded-Classification Pattern](coded-classification.md) applies the same law to
catalog codes and quoted evidence spans.

### 5. Reduce (optional)

If the primary findings still exceed one synthesis context, group the short
findings into bounded reduction batches and map a second judgement over those
batches. Repeat hierarchically only when needed.

Reduction may identify chronology, themes, disagreements, concentrated churn,
or unresolved anomalies. It must not replace or erase the primary per-item
findings. A reader must always be able to move from a reduced claim back to the
source item and its primary result.

Do not ask the model to compute totals. Counts and percentages come from the
reconciled manifest.

### 6. Render

Write two artifacts:

1. a complete machine-readable dossier containing the manifest, primary
   results, reductions, provenance, and coverage reconciliation;
2. a compact human index linking every synthesis claim back to primary results
   and source records.

Artifact existence and content are the success contract. A zero exit code
without the dossier is failure.

## Required invariants

A corpus map-reduce run must satisfy all eight invariants:

1. Every frozen input item or byte span belongs to exactly one primary map
   payload.
2. Every primary payload produces exactly one typed result.
3. Every primary result belongs to exactly one reduction batch when reduction
   is used.
4. Every model-emitted source ID is reconciled against collector-owned IDs.
5. Counts, coverage, hashes, and cost/call totals are computed in code.
6. Provider, model, corpus identity, and run identity are recorded.
7. No map failure or missing result is silently dropped.
8. At least one withheld known-truth (a hidden canary the initiator can
   verify independently) must surface in the results, matched by FAMILY
   rather than exact token; its absence invalidates the run before any
   artifact is emitted. Invariants 1–7 prove the run covered everything;
   only this one proves it judged anything correctly. Witnessed necessity
   (FR-893): a full-diary census satisfied invariants 1–7 while exact-label
   canaries found ZERO hits — total label drift (`tmp_msg_txt`,
   `stale_tmp_msg_file`, `tmp_msg_file_loss` for one trap) made the run
   semantically invalid despite perfect coverage arithmetic.

These are requirements, not optional hardening. If any invariant cannot be
proved, the output may still be a sample, but it is not an exhaustive corpus
analysis.

## Cost contract

Estimate the run before execution:

```text
primary_calls = primary_partitions
reduction_calls = sum(reduction_batches_at_each_level)
total_calls = primary_calls + reduction_calls
```

Also record the estimated input size per partition. A call count alone hides a
single overloaded partition.

Set hard ceilings for:

- source items and bytes;
- primary partitions;
- reduction batches and levels;
- total model calls;
- per-partition input size;
- wall-clock timeout.

The collector enforces the ceilings before the first model call. The renderer
records estimated and actual calls so later runs can audit the forecast.

## GitHub application A: descriptive recap

Use pull requests as the semantic unit when they exist. A pull request carries
a base/head boundary, discussion, checks, and often a governing issue. Fixup
commits are transport fragments; interpreting each as an independent intent
creates false narratives. A squash commit should link to or inherit the pull
request recap.

### Frozen PR input

- PR number and URL;
- repository identity;
- base and head SHA;
- title and body;
- linked issue, FR, or specification IDs;
- changed files and diff/stat payload;
- check results and merge state;
- collection timestamp and query/window.

### Primary PR recap

One typed result per PR:

```yaml
pr: 123
base_sha: "..."
head_sha: "..."
summary: "Introduces a reference-only corpus analysis pattern."
affected_surfaces: [reference, feature-request]
evidence: ["pull/123/files"]
uncertainty: "The linked issue does not state a rollout target."
```

The reducer may produce a release chronology, themes, churn hotspots, and
unresolved anomalies, but the complete artifact retains every primary recap.

When no PR grouping exists, use commit SHA as the identity and collect author,
date, subject/body, diff/stat, and linked issue or PR. State explicitly that
commit messages are descriptions by the change producer, not independent
statements of intended scope.

## GitHub application B: authority-aware scope reconciliation

"What changed?" is descriptive. "What changed that was not supposed to
change?" requires independent authority.

Keep two planes separate:

| Plane | Source | Question |
|---|---|---|
| Authority | Frozen FR + judgement, specification, or acceptance criteria | What was permitted or required? |
| Reality | Actual GitHub base/head diff and checks | What changed and what evidence exists? |

### Authority hierarchy

Use the strongest available source:

1. governing FR plus independent judgement or equivalent frozen
   specification;
2. issue/specification with testable acceptance criteria;
3. PR body with explicit in-scope and out-of-scope statements;
4. commit message.

Levels 3 and 4 are self-description from the change producer. Without level 1
or 2 authority, label findings `surprising` or `unexplained`, never
`unauthorized`.

### Primary reconciliation shape

```yaml
pr: 123
base_sha: "..."
head_sha: "..."
authority_sources:
  - feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md
  - feature-requests/FR-894-corpus-map-reduce-github-scope-reconciliation-reference.judgement.md
authorized_changes: []
unexplained_changes: []
missing_deliverables: []
out_of_scope_matches: []
evidence: []
confidence: high
```

Reconcile four classes:

- **Path drift:** changed paths lie outside an explicit scope fence.
- **Semantic drift:** an allowed file changed in a way authority does not
  permit.
- **Omission:** an authorized deliverable has no corresponding change or
  evidence.
- **Metadata drift:** PR body, head SHA, checks, local state, or linked
  authority disagree with GitHub reality.

Path matching can be deterministic. Semantic drift and omission usually need
an LLM judgement, but the reducer still owns source identity and coverage. A
model finding must cite both the authority clause and diff evidence that
support it.

### Review boundary

Cheap-model corpus analysis is triage and historical explanation. Its findings
are claims, not merge verdicts. A flagged live PR enters the independent
[`scripts/review.sh`](../../scripts/review.sh) route, which applies the
[PR Review Doctrine](../../.github/skills/review-pr/doctrine.md), runs relevant
validation, and leaves the merge decision to the human.

Do not weaken the reviewer by replacing its model, validation, or closed input
with the corpus classifier's cheaper contract.

## Privacy and egress boundary

Public GitHub history can be sent to an approved external provider. Private
repositories, customer code, secrets, personal data, and regulated material
require an approved provider or local model.

Before the model boundary, the collector must:

- exclude credential-bearing files and redact discovered secrets;
- omit binary patch bodies while retaining path, hash, size, and media type;
- cap oversized text patches and record the omitted spans;
- apply repository visibility and data-classification policy;
- avoid echoing private source text into public logs or final graph state;
- fail loudly when policy cannot classify an input.

The privacy policy is part of corpus freezing. Filtering after map fan-out is
too late.

## Operational checklist

Before running:

- [ ] Name the corpus, time window, and immutable identities.
- [ ] Bind or implement discovery and extraction adapters without copying the
  shared graph.
- [ ] Name the primary semantic unit (PR, commit, file, requirement, session).
- [ ] State the one judgement each map call makes.
- [ ] Set item, token/character, call, and timeout ceilings.
- [ ] Choose an approved provider/model for the data class.
- [ ] Decide whether the result is descriptive or authority-aware.
- [ ] Define deterministic reconciliation before writing the prompt.

After running:

- [ ] Verify all eight invariants.
- [ ] Read raw primary findings before trusting reductions.
- [ ] Confirm the complete dossier exists and carries provenance.
- [ ] Treat reduced totals as code-computed context, not model testimony.
- [ ] Route live PR findings to independent review.

## Precedents

- [FR-402 Prompt Theme Analyzer](../../feature-requests/FR-402-prompt-theme-analyzer-demo-implementation.md)
  and its [graph](../../examples/demos/prompt_theme_analyzer/graph.yaml): pinned
  Mercury-2 map classification, deterministic aggregation, semantic grouping,
  and rendering.
- [FR-748 FR Atlas](../../feature-requests/FR-748-fr-atlas-onboarding-summary.md)
  and its [graph](../../examples/demos/fr-atlas/graph.yaml): frozen FR corpus,
  chunk map, code-side coverage reconciliation, synthesis, and render.
- [FR-851 Requirement Witness Audit](../../feature-requests/FR-851-requirement-witness-audit.md)
  and its [graph](../../examples/demos/req_witness_audit/graph.yaml): bounded
  batches, typed findings, and rejection of missing or hallucinated IDs.
- [FR-884 Session Task-Shape Mining](../../feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md)
  and its [graph](../../examples/demos/session-shapes/graph.yaml): pinned Haiku
  map classification plus deterministic, privacy-scrubbed aggregation.
- [FR-892 Corpus Census](../../feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md),
  its [README](../../examples/demos/corpus_census/README.md), and
  [graph](../../examples/demos/corpus_census/graph.yaml): the shipped reusable
  discover-extract-map-reduce skeleton with invocation-bound adapters and a
  fail-closed ledger reducer.
- [FR-893 Diary Trap Census](../../feature-requests/FR-893-diary-trap-census.md)
  and its [aggregator](../../examples/demos/corpus_census/adapters/diary_recurrence.py):
  the pipeline's first production consumer — 1,266 entries in 24 batches
  (~$1, 26 min), distinct-entry recurrence counting, Scripture-key
  exclusion, public-safe committed artifact, and the witnessed firing of
  the hidden-canary invariant (exact-label match → 0 hits under total
  vocabulary drift; family matching required). Run via
  [scripts/diary_census.sh](../../scripts/diary_census.sh).
- [Recap graph](../../examples/demos/recap/graph.yaml): deterministic Git
  collection and one bounded synthesis judgement; useful for quiet windows,
  narrower than exhaustive per-item reconciliation.
- [PR Review Doctrine](../../.github/skills/review-pr/doctrine.md): the strong
  authority-versus-reality contract for one live PR, preserved as the merge
  review boundary.

FR-892 owns the executable generic census skeleton. The earlier
[FR-857](../../feature-requests/FR-857-corpus-analysis-fanout-graph.md) remains
parked for its question-first semantic-grep framing; this reference adds no
second runtime surface.
