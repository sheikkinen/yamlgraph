# Research record — durable keyed artifact store with deterministic gates

**Status: pre-FR.** This is a completed FR-890 sole-route research run with no
governing feature request yet. When the FR is filed, promote this record to
`feature-requests/FR-XXX.research.md` unchanged; the provenance line already
in `research-runs.jsonl` continues to reconcile against it.

- route: `scripts/research.sh` (FR-890 sole route), graph
  `examples/demos/research-route/graph.yaml`
- brief: `feature-requests/research-briefs/durable-keyed-artifact-store-brief.md`
- run date: 2026-09-04T04:30:11Z
- personas executed: os-infra-primitivist, data-process-planner,
  yamlgraph-native-planner, subtractionist, librarian
- provenance: `feature-requests/research-runs.jsonl` line stamped
  2026-09-04T04:30:12Z, `artifact_sha256 = d5baab89…fae2c456`,
  `brief_sha256 = 7a28e829…148cfad5`, `code_git_sha = 1d822d40…`
- **Known verifier discrepancy (Windows host):** `--verify-promotion` reports
  `mismatched` for any byte-faithful promotion on this host — the launcher
  hashes CRLF bytes, the verifier hashes LF-normalized text. Same defect class
  as the FR-955, FR-958, and FR-981 records; a separate FR is owed for the
  newline boundary. `--verify-artifact` on the appendix passes.

## Three runs were discarded before this one

The reducer refused three consecutive runs with
`precedent names nonexistent CAP-628`. A persona was converting the literal
`FR-628` token in the brief into a fabricated `CAP-628`; the registry holds no
such capability. The citation boundary was working exactly as designed —
model output is a claim until code resolves it — but the failure discards the
entire run, and it is **reproducible, not flaky**: retrying an unchanged brief
reproduced it twice. The fix was to remove the bare `628` token from the brief
and cite the gate node by graph path.

Operational note for future callers: on `precedent names nonexistent X`, edit
the brief to remove or fully qualify the identifier that X resembles. Do not
retry unchanged.

## Outcome

Five personas, five `pursue`, three solution classes. No dissent on whether
the shape exists; the disagreement is about what should carry it.

## The finding that matters

**Four of five personas answer `is_this_a_graph: YES`** — the durable store is
expressible in YAML: `write_data_file` persists keyed artifacts, a
`data_files` glob reads them back on a later run, and the integrity gates are
`type: python` *nodes inside the graph*.

This inverts `feature-requests/FR-981.research.md`, where four of five
answered **No** for the closely related question and concluded that retention
and staleness require Python ownership outside the graph boundary. That answer
was folded into FR-981, credited by its judgement, and merged.

The difference in method explains the difference in answer. FR-981's route
reasoned about the framework in the abstract and about `book-summary`'s
per-run `all_summaries` reducer. This route was pointed at two committed
graphs that already do it. Reasoning about what a framework can express lost
to reading what it already expresses.

## Solution classes (substance fold)

| class | mechanism | precedent | disposition |
|---|---|---|---|
| 1. Document a durable-keyed-store pattern with deterministic gates | `write_data_file` per key, `data_files` glob read-back, Python gate nodes rejecting invalid mutations before persist | CAP-173, CAP-174, CAP-181; `examples/demos/wiki-memory`, `examples/novel_fandom`, `examples/demos/write_data_file` | **CHOSEN** — three witnesses and three registered capabilities, better evidenced today than the phased-summary pattern it underpins |
| 2. Amend `reference/patterns.md` Pattern 7 rather than add a document | Pattern 7 "Stateful Memory (AgentState)" is in-run `messages`; a reader searching for persistence finds it first and is misdirected | `reference/patterns.md` | ADOPT AS PART OF 1 — rename or cross-reference is required regardless; it does not replace the pattern document |
| 3. Do nothing; the node-type reference suffices | `reference/graph-yaml.md` documents the syntax; the examples work | subtractionist, `growth_as_default`, `does_the_platform_already_do_this` | REJECTED, but its constraint is binding: document an existing working composition, claim no new capability, and write no framework code |
| 4. Frame it as Event Sourcing | append-only immutable event log; state derived by replay | https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing (librarian) | **REJECTED as a framing.** The witnesses overwrite keyed *current-state* documents; they keep no event log and derive nothing by replay. The nearer analogue is a validated repository with invariants. The citation is recorded; the terminology is not adopted. |
| 5. Framework primitive for the store | a keyed-store node type or helper | none | DEFERRED — four personas say YAML already expresses it, which is an argument against a primitive, not for one |

## Preserved disagreement

The subtractionist voted `pursue` while arguing the pattern be recorded as
"already working" rather than as a new capability. That is a scope constraint,
not agreement, and it binds: no CAP or REQ allocation, no framework change,
and an evidence grade that says three examples demonstrate this **today** —
unlike the phased-summary document, whose composition grade is UNEXERCISED.

## Prior art requiring disposition

Retrieval returned `FR-874-cross-device-agent-memory-sync.md` **[REJECTED]**.
A rejected FR is precedent: any FR filed from this record must distinguish
itself from FR-874's rationale or die by it. Not dispositioned here — that is
the filing FR's obligation.

Also returned: `FR-981-module-history-phased-summary-demo.md` and its research
record, which is the consumer this record corrects, and two plot_modeller FRs
(FR-590, FR-596) on the nouns "keyed/artifact/store" that appear to be
vocabulary collisions rather than problem matches.

## Raw route output (provenance appendix — byte-identical to the run artifact, LF-normalized)

# Draft alternatives

- brief: durable-keyed-artifact-store-brief.md
- run date: 2026-09-04T04:30:11Z
- personas executed: os-infra-primitivist, data-process-planner, yamlgraph-native-planner, subtractionist, librarian

### Prior art retrieved for this brief (filename-noun, IDF-ranked)
  FR-874-cross-device-agent-memory-sync.md  [REJECTED]  matches: durable, keyed, artifact, store
  FR-981-module-history-phased-summary-demo.md  [Judged]  matches: durable, artifact, store, brief
  FR-981.research.md  [?]  matches: durable, keyed, artifact, store, brief
  FR-590-plot-modeller-L5-multi-perspective.md  [Limbo]  matches: keyed, artifact, store
  FR-596-plot-modeller-L7-per-agent-affect-throughline.md  [Enforced]  matches: keyed, artifact, store

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Filesystem-keyed durable store with deterministic Python gate: write typed YAML per key via write_data_file, read accumulated set via data_files glob, reject model output violating schema or reference integrity before persist. | os-infra-primitivist | os-permissions | pursue | FR-625-write-data-file-tool.md, FR-629-data-files-glob-support.md, examples/demos/wiki-memory, examples/novel_fandom | yes | low/medium; mechanism already works in three committed examples. Risk is documentation scope: pattern doc, Pattern 7 rename, and FR-981 disposition require careful evidence grading per house convention. | Three independent graphs demonstrate this composition: identity as filesystem key, store outlives run, deterministic gate blocks corruption. Platform already enforces file ownership and read-back atomicity; no framework change needed. Witnesses contradict FR-981 "precedented zero times" claim, proving the pattern exists and merits indexed reference. |
| Index three committed examples (wiki-memory, novel_fandom, write_data_file) as a durable-keyed-store pattern with deterministic gates, separate from in-run state, in reference/patterns.md with evidence grade matching CAP-173, CAP-174, CAP-181. | data-process-planner | schema-data (convergent x2) | pursue | CAP-173 Write Data File Tool, CAP-174 Data Files Glob Support, CAP-181 Novel Fandom Genesis Pipeline, FR-981-module-history-phased-summary-demo.md (merged 2026-09-04 without surfacing these witnesses) | Yes. The durable store is expressible in YAML: write_data_file persists keyed artifacts, data_files glob reads them back, and deterministic Python gates validate before merge. Key ownership and staleness are graph-native, not Python-external. | Low effort, low risk. Three working examples exist; no framework code changes required. Risk is naming collision with Pattern 7 (Stateful Memory); rename or cross-reference Pattern 7 to in-run state only. | The three witnesses share identity-as-key, cross-run persistence, and deterministic validation gates—a shape absent from reference/patterns.md despite being precedented by committed CAPs. Documenting it dissolves the retrieval failure that led to FR-981's "zero precedent" judgment and prevents future readers from finding only Pattern 7's in-run state under a persistence-shaped name. |
| Document a "Durable Keyed Store" pattern: per-item identity ownership, cross-run persistence via write_data_file + data_files glob, deterministic gates (reference resolution, lane immutability) blocking invalid mutations before persistence. | yamlgraph-native-planner | schema-data (convergent x2) | pursue | FR-625-write-data-file-tool.md, FR-629-data-files-glob-support.md, examples/demos/wiki-memory, examples/novel_fandom | yes: wiki-memory-gate and novel_fandom both express durable keyed stores entirely in YAML using write_data_file, data_files glob, and deterministic Python gates—no framework primitives required. | low: three working examples exist; pattern document mirrors corpus-map-reduce structure with evidence grades from committed artifacts. | Three independent graphs demonstrate identical machinery: keyed file writes, glob-based reads, deterministic gates. Pattern document resolves naming collision with "Stateful Memory" and clarifies mechanism-based indexing for readers seeking persistence guidance. |
| Delete the pattern document. The three witnesses (wiki-memory, novel_fandom, write_data_file) already work in YAML. The node-type reference and examples suffice; no new shape exists. | subtractionist | subtraction | pursue | FR-981.research.md, growth_as_default, does_the_platform_already_do_this | Yes. The durable store is expressible inside a graph via write_data_file and data_files glob; key ownership and staleness are YAML-native, not Python-external. | Low. No code change required; only a decision to document the pattern as "already working" in the reference, not as a new capability. | The three committed examples demonstrate the full composition. Effort must stay proportionate to documenting existing machinery. If the node-type reference already suffices, research must say so rather than invent a pattern. |
| Event Sourcing pattern: append-only store records all state changes as immutable events; validation gates enforce invariants before events persist, enabling cross-run accumulation with deterministic integrity. | librarian | external-method | pursue | https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing | No. Event Sourcing is a persistence and validation pattern external to graph structure. The durable store and deterministic gates operate outside the graph's node-edge topology. | Low. Event Sourcing is a mature, well-documented pattern. Mapping wiki-memory and novel_fandom to Event Sourcing terminology requires documentation only, no framework changes. | wiki-memory and novel_fandom both implement Event Sourcing: immutable per-item files (events), deterministic Python gates (invariant validators), and cross-run accumulation. This precedent directly names the composition and resolves the naming collision with Pattern 7. |
