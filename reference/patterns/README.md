# Pattern Catalogue

Eight documented architectures for placing nondeterministic model judgement
inside deterministic control. Each answers a different ownership question;
choose by what your result must *prove*, not by what the topology looks like.

The recurring rule across all eight:

> The model supplies bounded semantic judgement. Code owns identity,
> completeness, time, policy, and irreversible effects.

For the fourteen smaller building-block patterns (linear pipeline, routing,
reflexion loop, tool agent, map fan-out, guardrails, boundary coercion, …) see
[Common Patterns](../patterns.md). Those are node-level recipes; the eight
below are system-level ownership contracts that compose them.

## Selection by required proof

| Your result must prove that… | Pattern |
|---|---|
| every item in a finite corpus received a bounded judgement | [Corpus Map-Reduce](corpus-map-reduce.md) |
| every code and evidence span resolves to an authoritative vocabulary | [Coded Classification](coded-classification.md) |
| every runtime-selected input produced a result or a typed failure | [Batch Runner](batch-runner.md) |
| every required field is validly resolved through conversation | [Schema-Driven Extraction](schema-driven-extraction.md) |
| every rollup claim traces through a durable brief to a source record | [Phased Summary](phased-summary.md) |
| a semantic verdict routes progression explicitly | [LLM-as-Gate](llm-as-gate.md) |
| every external event has a legal lifecycle transition | [FSM-as-Conductor](fsm-as-conductor.md) |
| every failure preserves the prior default before a deadline | [Deadline-Bounded Enrichment](deadline-bounded-enrichment.md) |

## Families

| Family | What code owns | Patterns |
|---|---|---|
| **Population** — judge many things once | coverage, identity, arithmetic | Corpus Map-Reduce, Coded Classification, Batch Runner |
| **Accumulation** — judge one thing over time | convergence, substitution, provenance | Schema-Driven Extraction, Phased Summary |
| **Control** — decide whether, when, how long | routing, lifecycle, deadlines | LLM-as-Gate, FSM-as-Conductor, Deadline-Bounded Enrichment |

Patterns compose across families: a coded classifier runs on corpus
map-reduce; a schema-driven interview is one cognitive action inside an FSM;
a phased summary uses hierarchical reduction when one subject exceeds a
context window.

## Comparative map

| Pattern | Governing question | Core topology | Primary hazard |
|---|---|---|---|
| Batch Runner | How do we run one pure graph over runtime-selected files? | compile once → load and transform → invoke per input → one result per input | swallowed failures; ambiguous `null` outputs |
| Corpus Map-Reduce | Did we judge every item in a finite corpus? | freeze → partition → typed map → reconcile → optional reduce → render | complete coverage with semantically worthless findings |
| Coded Classification | Which authoritative catalogue entries fit this text? | build catalogue → clustered map → reconcile claims → evaluate | fabricated evidence; broad codes; imported model priors |
| Schema-Driven Extraction | Which required facts are still missing? | schema → extract → detect gaps → probe → interrupt → repeat → recap | syntactic completion mistaken for semantic completeness |
| Phased Summary | What must future readers retain about an evolving subject? | record → durable brief → subject store → rollup | silent information loss at the substitutive brief |
| LLM-as-Gate | Does this artifact semantically satisfy a condition? | structured verdict → router → branch | forced confidence; plausible wrong verdicts |
| FSM-as-Conductor | Who owns event-driven lifecycle around cognitive work? | FSM → async graph action → completion event → transition | ambiguous events; duplicate launches; lost resume state |
| Deadline-Bounded Enrichment | Can optional judgement improve an action without delaying it? | committed record → async enrichment → CAS block → deadline or default | races; duplicate action; wrong deadline arithmetic |

## Evidence vocabulary

Every pattern document should state its grade in an `**Evidence base:**`
callout near the top. The vocabulary:

- **Proven** — at least two materially independent implementations, with
  observed failures that shaped the pattern.
- **Exercised** — one working implementation with tests or operational
  evidence.
- **Provisional** — one instance, or a composition supported mainly by
  external precedent.
- **Proposed** — coherent design without an end-to-end witness.

Grades as stated by each document today:

| Pattern | Stated grade |
|---|---|
| Corpus Map-Reduce | proven (multiple instances) |
| Coded Classification | proven (two instances) |
| Phased Summary | two claims, graded separately — see document |
| Deadline-Bounded Enrichment | single instance; explicitly provisional |
| Batch Runner | not stated |
| FSM-as-Conductor | not stated |
| LLM-as-Gate | not stated |
| Schema-Driven Extraction | not stated |

A missing grade is a gap in the document, not a verdict on the pattern.

## Cross-pattern laws

1. **Models produce claims, not facts.** Codes, IDs, quotations, dates, and
   totals are reconciled against deterministic authority.
2. **Identity precedes inference.** Freeze paths, hashes, record IDs, schema
   and catalogue versions before model work.
3. **Completeness and correctness are different axes.** Coverage arithmetic
   proves traversal; a canary, fixture, or raw read proves detection.
4. **Failure stays typed and visible.** Missing, malformed, abstained,
   defaulted, and provider-failed are different outcomes; do not collapse
   them to `null`.
5. **Deterministic rules belong in code.** Counts, set differences, taxonomy
   constraints, deadline arithmetic, and deduplication are not prompt work.
6. **Cost is part of correctness.** Partition sizes, call ceilings, and
   timeout relationships belong in the pre-run contract.
7. **Privacy classification happens before egress.** A brief inherits its
   source's data class; a claim-check token does not declassify.
8. **Irreversible effects stay outside model authority.** Models write
   verdicts, briefs, classifications, and enrichment blocks; deterministic
   actors apply policy and act.

## Adding a pattern

A document belongs here when it has: a distinction that changes an
implementation decision; at least one working YAMLGraph witness; a named
failure mode or incident that shaped it; deterministic invariants that can be
tested; and a comparison explaining why the nearest existing pattern is
insufficient. Otherwise it is a research note, not a pattern.

Each new document gets a row in every table above and a row in the parent
[reference index](../README.md).
