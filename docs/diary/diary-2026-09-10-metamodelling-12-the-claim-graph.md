# The claim graph: history as a requirements matrix with two edges the repo skipped

**Date:** 2026-09-10
**Series:** metamodelling, part 12 (applied)
**Trigger:** operator: "history would be modelled with shitload of
interconnected claims. notes the parallel to CAP, REQ — architectural
claims. history would be quite a model. A. vector database?"
**Context:** part 11 built one ledger and found the oracle for history is
structural — a rung computed from latency, origins, transmission. This
entry takes the operator's restatement seriously: the ledger is one row
of a graph, and the graph already exists in this repository at small
scale under other names.

## The parallel

| Repo RTM | History model |
|---|---|
| CAP, capability claim | interpretation / narrative claim |
| REQ, requirement | fact claim, typed |
| test with `@pytest.mark.req` | passage that attests the claim |
| `req_coverage.py --strict` | the reduce: every claim ≥ 1 attesting passage; every passage → ≥ 1 claim |
| test → module → git blob | passage → work → manuscript |
| test author | work author, with floruit and agenda |
| — | **contradicts**: Livy vs Polybius on Hannibal's numbers |
| — | **derives_from**: Livy ← Polybius ← Fabius Pictor; chain latency lives here |

Two edge types the repo's matrix does not have, and history cannot do
without either. That is why it is "quite a model": the edges the repo
skipped are the ones that carry most of the field's knowledge. It also
says something about the repo — a REQ derived from another REQ, or a test
that contradicts another test's assumption, has no place to be recorded.

## Schema first; the store follows

```yaml
nodes:
  Claim:      {id, text, type: fact|interpretation|legend|counterfactual, period, event_date?}
  Passage:    {id, work, locator, text, url, verified: bool}
  Work:       {id, author, title, composed_date, survives: full|partial|fragments|lost}
  Author:     {id, floruit, agenda: participant|partisan|courtier|hostile|compiler}
  Manuscript: {id, work, date, exemplar?}
  Concept:    {id, term, first_attested}          # anachronism check
edges:
  attests      Passage -> Claim
  contradicts  Passage -> Claim | Claim -> Claim
  derives_from Work -> Work                       # Quellenforschung
  transmits    Manuscript -> Work
  interprets   Claim -> Claim
  uses_concept Claim -> Concept
derived, never stored:
  latency        = author.floruit - claim.event_date
  chain_latency  = min latency over derives_from ancestors
  origins        = components of attesting passages after collapsing derives_from
  transmission   = count(Manuscript) reachable via transmits
  verdict        = f(type, latency, chain_latency, origins, contradicts)
```

Every metric from part 11 is a path query: reachability, shared
ancestor, component count. That decides the store before any product
name is said.

## A. Vector database — partly, never as the system of record

**Where similarity is the question.** The sentence → candidate passage
link (retrieval step of Quellenforschung) and near-duplicate claim
detection. A vector index is right there, and `vectorstore/` already
exists in the repo.

**Where similarity is the wrong answer.** `attests` versus
`contradicts`: a contradiction is maximally similar and opposite in
sign. `derives_from`: Livy paraphrasing Polybius embeds close, and that
closeness is the *question*, not the answer. Origin counting and chain
latency are graph walks. Scripture already names the trap —
`false_duplicate`, "syntactic similarity ≠ semantic equivalence". A
vector store as truth yields a model that cannot tell "Livy agrees with
Polybius" from "Livy copied Polybius" from "Livy contradicts Polybius".

**What the platform already does.** Wikidata's statement model: item,
property, value, *references*, *qualifiers*, *rank* (preferred / normal
/ deprecated). Rank is the rung; references are `attests`; qualifiers
carry the date and the source. Pleiades (places), Trismegistos (people
and texts), PHI (inscriptions) are the linked catalogues. The graph
largely exists as linked open data. What is missing is the claim layer
for a *curriculum's* sentences and the `derives_from` layer for
historiography.

**Decision.** Typed edge table as the system of record — SQLite:
recursive CTEs handle chain latency and reachability, the repo ships
SQLite checkpointers already, Pydantic models over rows satisfies
Commandment 5. Scales to $10^5$–$10^6$ claims, which is all of Roman
history, not one course. Vector index as a derived, rebuildable artifact
over Passage and Claim text, consulted only at the retrieval boundary. A
property graph only if path queries dominate and the CTEs measurably
slow — a measured switch, not a first choice.

**Scale check.** A high-school Rome course is roughly 2–5k claims, 500
passages, 50 authors. That fits YAML files with the same tooling as
`capabilities/`. The vector question does not arise until the corpus
does.

## What this returns to the series

1. **The oracle is a graph, and the graph is an RTM.** Part 11's
   "structural oracle" is a coverage check with two more edge types.
   Fields that already have a requirements matrix have most of the
   harness; the increment is `contradicts` and `derives_from`.
2. **Store follows query.** Naming the derived metrics first made the
   store decision mechanical. Part 1's rule 1 — write the check before
   the artifact — applied to infrastructure.
3. **Similarity is a retrieval boundary, not a truth boundary.** The
   vector index earns its place at exactly one edge of the pipeline and
   is dangerous everywhere else. `false_duplicate` at system scale.

## Traps

**`similarity_as_support`.** Treating embedding proximity as `attests`.
The passage that contradicts the claim is the nearest neighbour.

**`store_before_query`.** Choosing a database from the shape of the data
instead of the shape of the questions. The claims *look* like documents;
the questions are all paths.

## Heuristic

Write the derived metrics as queries before naming a store; if they are
paths, the record is a typed edge table, and any index is a cache. Then
check whether Wikidata already has the nodes.

**Seed:** the repo's own RTM lacks `contradicts` and `derives_from`.
Which REQs in `ARCHITECTURE.md` were derived from earlier REQs, and which
tests encode assumptions another test contradicts? A one-day pass over
`capabilities/` with the history schema would say whether the two edges
the repo skipped are absent because unneeded or because unrecorded.
