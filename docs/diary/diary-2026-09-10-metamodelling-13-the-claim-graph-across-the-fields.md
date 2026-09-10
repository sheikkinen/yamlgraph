# The claim graph across the fields: liability draws the edges

**Date:** 2026-09-10
**Series:** metamodelling, part 13 (applied)
**Trigger:** operator: "reflection — would that claim graph model help in
software engineering" → "continue to the other fields analyzed. write a
diary."
**Context:** part 12 derived a claim graph from history (typed claims;
`attests`, `contradicts`, `derives_from`, `transmits`; a rung computed
from latency, origins, transmission; `legend` as a type; `agenda` on the
author). This entry asks, for each field in the series, whether the
graph would help, what the field already has, and what one query would
pay first.

## Software engineering (this repository)

Every node and edge type maps; almost none is data.

| Model | Repo | State |
|---|---|---|
| `attests` | test → REQ; demo‑output.log → graph.yaml | first recorded; second inferred from file location — `proof_by_placement` was this edge being fakeable |
| `contradicts` | rejected FR as precedent (FR‑737); conflicting Scripture entries | found by the judge each time, never recorded |
| `derives_from` | FR folds; Scripture trap ← diary ← incident; the `(FR‑…)` parentheticals | prose citations, unqueryable |
| `transmits` | artifact → producing SHA | the `artifact_carries_code_identity` seed |
| latency | last attested → now | the census's *last‑fail* column |
| origins | tests sharing one fixture or mock = one witness | never computed; `mock_escape_hatch` is the symptom |
| `legend` | constraints with no citable origin | present, unnamed |
| `agenda` | human / agent / vendor as claim author | doctrine says treat agent output as adversarial; no field records it |

Where it pays, ranked by first consumer: Scripture provenance (entries
with zero traceable incident, or incidents from one origin — the judge
on the next Scripture‑editing FR); staleness as latency (the census);
witness independence in `req_coverage.py` (tests grouped by shared
seams); recorded contradiction at judgement time. Where it does not:
code correctness — tests are already a complete cheap oracle — and as a
system: 2–5k nodes is YAML fields plus one script, and declared edges
that nobody produces at a boundary are `gate_checks_shape_not_substance`.

Honest test: the first query ("which Scripture entries cite no FR or
diary?") is a grep. Run it by hand; build fields on the second question.

## Mathematics

**Already has it, completely, where formal.** Mathlib's dependency graph
is `derives_from` under a total oracle. **Where informal:** the citation
graph of papers has `derives_from` but no propagation — a lemma found
flawed does not flag the papers built on it; readers discover the
dependency by hand. The "obviously" step is an `attests` edge with no
passage at its end: `legend` inside a proof. First query: given a
retraction or a found gap, list downstream results. First consumer: the
referee of any paper citing the retracted one.

## Law

**Has the most complete claim graph of any field, commercially, for a
century and a half.** Citators (Shepard's from the 1870s, KeyCite) are
exactly `attests` / `contradicts` / *overruled* edges between cases with
a **computed status** — the red flag — that propagates: overrule a
holding and every case resting on it is marked. `derives_from` is the
precedent chain; latency is the age of authority; `transmits` is the
reporter series. *Mata v. Avianca*'s six cases would have returned "node
does not exist" in seconds. The gap was never the graph; it was that the
citator is a paid product not wired to the drafting boundary — part 3's
`last_boundary_first_oracle`. What law gives the model: **status
propagation** as the query that justifies the edges.

## Journalism

**Fragments exist.** ClaimReview structured data (claim, claimant,
rating, reviewer) is a claim node with an `attests`/`contradicts` edge
to a fact‑check; C2PA is `transmits` for images. **The missing edge is
`derives_from` between stories** — the press‑release origin problem.
Two outlets, one wire, counted as two: `counted_not_independent` is
precisely an unrecorded `derives_from`. First query: collapse
republication chains and report origins per claim. First consumer: the
fact‑checker at deadline — which means the graph must be populated
*before* deadline, or it is the expensive check that gets dropped
(part 5).

## Clinical practice

**The most mature instance outside law, and the only one with `agenda`
declared.** Systematic reviews are `derives_from` with a computed rung
(GRADE); trial registries are pre‑committed claim nodes (the RED test
with a timestamp); conflict‑of‑interest declarations are the `agenda`
field made mandatory; interaction databases are `contradicts` edges
evaluated at the order boundary. **Two gaps.** Retraction does not
propagate: the 1998 *Lancet* paper linking MMR to autism was retracted
in 2010 and its downstream claims persist in the population's beliefs
and in secondary literature — a red‑flag propagation the field lacks.
And chain latency evidence → guideline is long; a commonly cited
estimate for research‑to‑practice is around seventeen years. First
query: for each guideline recommendation, the latency of its most
recent supporting node. First consumer: the guideline committee.

## Strategy

**Weakest graph; highest `legend` density.** Decision journals are
isolated nodes with no edges. The assumption register is the node list
without `derives_from` to the decisions resting on each assumption.
"Customers want X" is `legend` in most organisations — no origin
anyone can cite. Base rates are `attests` edges from a reference class
and are rarely drawn. The graph's one high‑value query: **when an
assumption is falsified, which decisions are downstream?** — propagation
again. First consumer: the scheduled reread (part 7). Without the edges,
the reread scores decisions one at a time and misses the common cause.

## Witchcraft

**Had the graph.** The *Malleus* cites authorities; trials cite
precedents; `derives_from` was dense and the citations were real —
to Augustine, to Aquinas, to earlier trials. The `attests` edges
terminated in the ordeal, the spectral witness, and the confession under
pressure: nodes no third party could inspect and no observation could
fail. **The graph amplified.** Each conviction became an attesting node
for the next; propagation ran forward on false positives with nothing
running backward. The model's safeguard, stated as a constraint:
*every `attests` edge terminates in a Passage a third party can
inspect, and every rung has a recorded fail.* The graph structure is
neutral; the oracle at the leaf is everything. A claim graph with fake
leaves is a well‑organised delusion with excellent traceability.

## What the fields return, together

1. **Liability draws the edges.** The graph exists, mature and
   propagating, where wrong claims cost money or lives: law, medicine,
   formal proof. It is absent where claims are cheap and unaccountable:
   strategy, republished news, SE doctrine, agent output. The LLM moves
   claim production into the cheap‑and‑unaccountable region at scale,
   which is the argument for drawing the edges there.
2. **Propagation is the query.** Every field's first payoff is the
   same: a node is refuted, retracted, overruled, or falsified — flag
   what derives from it. Law has it; medicine and mathematics partly;
   strategy and SE not at all. Edges without propagation are
   documentation; edges with it are a harness.
3. **Pre‑committed nodes are one type.** Trial registration, decision
   journal entry, RED test, formal statement, dated forecast: a claim
   stamped before the outcome. The graph should know the type so the
   reread can find them.
4. **`agenda` is declared in exactly one field.** Medicine makes
   conflict of interest a required field. Everywhere else it is
   inferred. For agent‑authored claims the field is cheap and the
   doctrine already demands the inference.
5. **The leaf is the oracle.** Witchcraft is the proof: a complete graph
   with uninspectable leaves converges confidently on error. The
   constraint belongs in the schema, not in a guideline.

## Traps

**`edges_without_propagation`.** Traceability recorded but never walked
backward. Looks like a harness, behaves like an archive.

**`graph_as_oracle`.** Trusting the structure because it is dense and
well‑cited. Density measures effort, not contact with the world.

## Heuristic

Before adding an edge type, name the propagation query that will walk
it and who runs that query on what event. Before trusting a graph, check
the leaves: inspectable artifact, recorded fail. Then, and only then,
count the citations.

**Seed:** the propagation query for this repository — "FR‑X rejected or
superseded: which Scripture entries and open FRs derive from it?" — can
be answered today by grep over parentheticals for one FR. Run it for
the three most recently superseded FRs. If any Scripture entry rests on
a superseded FR, the `derives_from` field earns its place and the first
consumer is the prune.
