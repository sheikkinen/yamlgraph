# Problem brief: graphs that keep typed artifacts across runs are composed independently and documented nowhere

**Prior art:** `reference/graph-yaml.md` documents `write_data_file`
(FR-625) and `data_files` (FR-629) as node/directive **syntax**.
`reference/patterns.md` Pattern 7 "Stateful Memory (AgentState)" documents
in-run message accumulation only. `reference/compaction-pattern.md` (FR-616)
compresses state inside one run and persists nothing.
`reference/patterns/corpus-map-reduce.md` freezes a corpus and renders a
dossier but retains no per-item artifact for a later run to reuse.
`reference/patterns/phased-summary.md` (uncommitted draft, governed by the
merged FR-981) *depends* on this mechanism and describes it as unprecedented
in this repository — a claim this brief exists because it was wrong.
`docs/plan-fandom-architecture.md` and `docs/plan-fandom-generation.md`
discuss the mechanism as design for one example, not as a reusable shape.
A REJECTED-FR sweep found no prior proposal to document cross-run artifact
persistence as a pattern.

## Problem statement

At least three committed graphs independently compose the same machinery:
the graph writes one typed file per key, a later run reads those files back,
and deterministic Python refuses model output that would corrupt the store.

`examples/demos/wiki-memory` writes `wiki/<id>.yaml` per page via
`write_data_file`, reads the accumulated set through a `data_files` glob, and
runs a Python gate that rejects any drafted page whose references do not
resolve to an existing page, looping to a fix node on failure. Its README
states the cross-run contract directly: each run grows the wiki and
subsequent runs can reference pages created by earlier runs.

`examples/novel_fandom` keeps `canon/character/*.yaml` and
`canon/event/*.yaml` — a typed, entity-keyed canon accumulated by a loop
under two deterministic gates: no orphan references, and lane immutability,
where pages marked `lane: static` cannot be overwritten by the LLM.

`examples/demos/write_data_file` demonstrates the read-augment-write-back
cycle in isolation.

Three properties recur across all of them and appear in no pattern document:
identity is a key the graph owns rather than a position in state; the store
outlives the run that wrote it and is an input to the next; and a
deterministic gate stands between model output and the store, so a
hallucinated reference or an overwrite of protected material fails loudly
instead of persisting.

The absence has a measured cost. A pattern document and its governing FR were
researched, judged twice, and merged to `main` on 2026-09-04 while grading
this exact machinery — a durable per-item store and a deterministic
"every claim resolves to a stored artifact" gate — as precedented zero times
in this repository. Two committed witnesses contradicted that grade. The
author's searches were keyed on the subject vocabulary of summarisation and
never on the mechanism, and no index existed that would have answered a
mechanism-shaped question.

A reader looking for persistence guidance today is served worse than
randomly: `reference/patterns.md` offers "Stateful Memory", which is
in-run conversation state and answers a different question under a name that
promises this one.

The open question is what should carry these three properties: a pattern
document, a framework primitive, an amendment to existing node-type
reference, an index that makes graphs searchable by mechanism, or nothing at
all because the syntax reference is sufficient and the recurrence is
coincidence.

## Classification

judgement/analysis/generation

## Constraints

- Reference-and-example surfaces only. Any conclusion that framework code
  under `yamlgraph/` should change is a separate judged scope with its own
  witnesses; it may be recommended, not performed.
- Any document produced must carry an evidence-base grade in the house
  convention used by `reference/patterns/corpus-map-reduce.md`, and the grade
  must match what committed artifacts actually demonstrate.
- The relationship to the merged FR-981 phased-summary work must be
  dispositioned explicitly: whether that pattern is a specialisation of this
  one, a peer, or a duplicate that should be folded.
- The relationship to `reference/patterns.md` Pattern 7 must be
  dispositioned: amend, cross-reference, or rename, because the current name
  captures readers looking for the other thing.
- The deterministic gates in the witnesses (reference resolution, lane
  immutability) must be classified as part of this shape or as a separate
  one; `reference/patterns/llm-as-gate.md` already covers *semantic* gating
  and these gates are not that.
- No new CAP or REQ identifier may be invented; identifiers come from the
  FR-975/FR-980 reservation route.
- Effort must stay proportionate to documenting an existing, already-working
  composition. If the honest disposition is that the node-type reference
  already suffices and no pattern exists, the research must say so.
- `is_this_a_graph`: must be answered — whether the durable store is
  expressible inside a graph, or whether key ownership and staleness are
  necessarily Python outside it. Four of five personas answered "no" for a
  closely related question in `feature-requests/FR-981.research.md`, and the
  two witnesses here appear to contradict them by doing it in YAML.

## Witnessed incidents

- `examples/demos/wiki-memory/README.md`: "Demonstrates inter-run state
  accumulation with a deterministic integrity gate", flow
  `draft -> gate -> (valid) persist | (invalid) fix -> gate` with loop limit
  2, and a features table citing the `data_files` glob
  (`feature-requests/FR-629-data-files-glob-support.md`), the
  `write_data_file` tool (`feature-requests/FR-625-write-data-file-tool.md`),
  the deterministic Python gate node (`examples/demos/wiki-memory/graph.yaml`),
  and inter-run state chaining. Three seed pages ship with the demo. Every
  identifier in this brief is a feature request; none is a capability, and no
  CAP identifier above CAP-93 exists in this repository.
- `examples/novel_fandom/README.md` (FR-655): genesis pipeline persists
  structured output to `canon/` subdirectories; the accumulation loop is
  governed by "No orphan references — every `references` entry resolves to an
  existing page" and "Lane immutability — `lane: static` pages cannot be
  overwritten by LLM". The committed canon holds eight character files and
  multiple event files.
- `examples/demos/write_data_file/README.md` (FR-625): read-augment-write-back
  in isolation.
- 2026-09-04, PR #580 merged: `feature-requests/FR-981-module-history-phased-summary-demo.md`
  states that the store, the invalidation rule, and the incremental call
  count are "precedented zero times", and its judgement approved that framing
  after reviewing the repository. Neither the author, the five-persona
  research route, nor two judge executions surfaced `wiki-memory` or
  `novel_fandom`.
- 2026-09-04, mechanism-keyed grep: `write_data_file`, "inter-run",
  "cross-run" appear in `reference/graph-yaml.md`, `reference/module-map.md`,
  the uncommitted phased-summary draft, and several `docs/plan-*.md` design
  documents — and in neither `reference/patterns.md` nor
  `reference/README.md`, which is where a reader looks for a shape.
- `reference/patterns.md` Pattern 7 "Stateful Memory (AgentState)" documents
  `messages` with an `add_messages` reducer and a `type: agent` node — in-run
  state under a name a reader searching for persistence will find first.
