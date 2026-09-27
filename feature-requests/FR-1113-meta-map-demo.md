# Feature Request: Meta-Map Demo — Map-Reduce Census of the Repository's Own Map Graphs

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented (enforced 2026-09-27; PR pending)
**Enforce decisions (2026-09-27):** the operator gave `enforce` without
overriding Q-1, Q-2 or Q-4, so the recommended option (a) is recorded
for each. H-1: the real smoke run uses `inception/mercury-2.5`, as
pinned by the operator, and its provider spend is authorized by the
`enforce` verdict. Plan and implementation ship in one PR; there is no
separate `doc pr`.
**Judge run (2026-09-27, copilot backend, APPROVED WITH REVISIONS):**
the operator discarded it as advisory. Only its defect findings were
folded: the subgraph mappings (R-3); failure rendering from
`MapFailure` fields and path by index (R-4); counts computed at run
time (R-5); the declaration-vs-observation witness for timeout and
concurrency (R-6); and `flatten_output` added to the known gaps (from
R-1). R-1's narrowing of the intent was refused. The intent below
stands unchanged.
**Effort:** 1–2 days
**Requested:** 2026-09-27
**Intent:** meta-map demonstrates the map functionality in full. Every
map key and every branch outcome that the runtime supports today is
exercised in one real run, and a test proves each one (see the
[Coverage matrix](#coverage-matrix)). The inventory of the repository's
own map graphs is the corpus the demo runs on, not its purpose.
**First consumer / first event:** a graph author who opens the map
section of `reference/graph-yaml.md` and follows its "full example"
link, the moment they need `failures`, `min_success` or `on_overflow`
(today only `map-timeout` sets any of them). Secondary: the operator,
the next time a map contract FR (FR-1076, FR-955, FR-957) needs the list
of affected graphs. That list was built by hand as the 47-row
[FR-1073 migration census](FR-1073-map-result-contract.md#migration-census).
**Research:** in-body — [Alternatives Considered](#alternatives-considered)
(a dispositioned alternatives table, which the template accepts in place of
a `.research.md` record. No `scripts/research.sh` run.)
**Prior art:**
- [FR-1073](FR-1073-map-result-contract.md) — its migration census was
  written by hand. This FR produces the same kind of inventory
  (graph, map node, sub-node type, declared keys) with a graph.
- [FR-939](FR-939-map-overflow-policy.md) — provides `on_overflow`. This
  demo uses the feature and does not change it.
- [FR-944](FR-944-map-to-map-index-attribution.md),
  [FR-984](FR-984-map-fan-out-max-concurrency.md),
  [FR-1085](FR-1085-default-max-concurrency.md) — runtime map
  features used as they are. No changes.
- [FR-1063](FR-1063-map-compiler-package-split.md) /
  [FR-1064](FR-1064-map-branch-contract.md) (REJECTED/SPLIT) — both
  changed the compiler. This FR touches no code under `yamlgraph/`, so
  neither rejection applies.
- `examples/demos/pipeline_audit/` — an agent chooses when to call
  `scan_graphs_tool`, and the graph has no map node. This FR discovers
  graphs in a deterministic Python node, then runs map → reduce.
- `examples/demos/diary_index/`, `examples/demos/corpus_census/`,
  `examples/demos/person_profile_census/` — same shape (discover →
  map → reduce) over other corpora. This FR reuses the shape, not the
  code. See Q-1 on reusing census adapters.
- `examples/demos/map/`, `examples/demos/python-map/`,
  `examples/demos/map-timeout/` — each shows one map feature. This demo
  uses the result contract and the overflow policy together in one graph.

## Summary

`examples/demos/meta_map/` demonstrates the map node in full by running
it over the repository's own map graphs. The graph has five nodes:

1. **Discover (Python).** Walks `examples/` and `graphs/`, parses every
   `*.yaml` file, and returns the paths of the graphs that have at least
   one `type: map` node. This step only selects paths.
2. **Poison the source (Python).** Appends three paths that are known
   to be wrong, taken from `poison.yaml`, a data file the graph loads
   through `data_files`:
   - `examples/demos/hello/graph.yaml`: a valid graph with no map node.
   - `feature-requests/FR-1113-meta-map-demo.md`: this FR, which is not
     a graph.
   - `yamlgraph/compile/map_compiler.py`: the map implementation itself,
     a Python script and not a graph.

   These are bad data fed to the LLM on purpose. Nothing marks them
   as poison anywhere the LLM can see.
3. **Summarize (map, subgraph sub-node, one branch per path).** Each
   branch runs a three-node subgraph:
   - `read_source` (Python) is a plain file reader. It returns the path
     and the raw text. It fails only on I/O and never judges the
     content, so the LLM receives the bad data as it is.
   - `describe` (LLM) reads the raw text and returns a typed **claim**:
     `map_nodes: list[str]`, a one-sentence intent, and one sentence on
     the map's role. The schema has no "not applicable" answer, so the
     LLM can never classify an input as not a map graph. Given bad data
     it either fails on its own (schema or provider error) or produces a
     description of a map graph that does not exist.
   - `reconcile` (Python) grades the claim. It parses the same text
     independently. `map_nodes` must equal the parsed set of map node
     names, and that set must not be empty. Otherwise it raises
     `ClaimMismatchError` with the claim and the parse in the message.
     On a match it adds what the parse knows for certain: sub-node type,
     declared keys, and **map version**. This applies the Scripture cure
     `two_strike_split` ("treat the model's output as a CLAIM reconciled
     against the source of truth at the boundary"). The LLM is examined
     by a key it never sees; the input is not cleaned before the LLM
     reads it.
4. **Reduce (LLM).** One call writes a summary text from the successful
   branch records and from counts computed in Python. A Python
   `prepare_reduce` node (`reduce_inputs`) computes those counts and
   the record list first, so the LLM never counts (decided at
   enforce).
5. **Render (Python).** Writes `outputs/meta_map/report.md`: a coverage
   line built from `_map_verdict`, a table with one row per successful
   branch ordered by `_map_index`, the reduced summary, and a failures
   section built from the typed `MapFailure` channel. A failure's path
   comes from `state.paths[MapFailure.index]`. Its detail is
   `MapFailure.message` verbatim, never parsed back: `ClaimMismatchError`
   messages carry both the claimed and the parsed node names.

**Run outcome:** the counts come from the run, not from this FR. With
`real = len(discovered paths)`, `dispatched = real + len(poison)` and
`required = ceil(0.9 × dispatched)`, the three poisoned branches always
fail: either the LLM errors, or `reconcile` rejects its claim because
the parse finds no map nodes. The interesting output is *how* each one
fails, which is recorded verbatim. Misreads of real graphs add to the
failure count. The run exits 3, "completed with errors" (FR-1097), while
`dispatched − failed ≥ required`, and raises `MapCompletenessError`
otherwise. The report and the README print the computed values.

## Value Statement

Before a map contract change, the operator can generate the list of
affected graphs in one run instead of writing it by hand. Graph authors
get one demo that uses the FR-1073 and FR-939 map features together.

## Problem

- Map behavior changed eight times in September 2026 (FR-939, FR-944,
  FR-984, FR-1073, FR-1085 shipped; FR-955, FR-957, FR-1076 are pending).
  Before this FR, the only full inventory of map-using graphs is FR-1073's
  hand-written census. It is already out of date: `grep -rlE
  'type:\s*map' examples graphs` returns 58 files. The census has 47
  map-node rows.
- Of those 58 files, only `examples/demos/map-timeout/graph.yaml` matches
  `failures:|min_success|on_overflow`. No example uses the new map keys
  together, so authors copy the older, minimal key set.
- The map key table in `reference/graph-yaml.md` explains each key but
  gives no example that uses all of them.

## Ideal Result

One graph, run for real, uses every map feature the runtime offers
today. A reader can see each feature's effect in the output: fan-out,
a subgraph per item, the item cap and overflow policy, per-branch
timeout, typed failures kept out of `collect`, the completeness
threshold, the verdict, index ordering, and bounded concurrency. The
poisoned inputs reach the LLM unfiltered. The failures channel then
carries real failures, which are LLM claims contradicted by the source,
instead of failures staged by the demo's own guard. The report is also
useful in its own right: every map graph in the repository, with its
intent and declared map version, plus a summary.

## Proposed Solution

### Coverage matrix

| Map feature | Where in the demo | Witness |
|-------------|-------------------|---------|
| `over` / `as` / `node` / `collect` | `summarize` | AC-6 |
| subgraph sub-node (FR-202) | `read_source` → `describe` → `reconcile` per branch | AC-4 |
| `max_items` + `on_overflow: error` (FR-939) | cap 100 on `summarize` | AC-5 |
| `timeout` (FR-069) | 120 s per branch | AC-11 |
| `failures` typed `MapFailure` channel (FR-1073) | `ClaimMismatchError` from `reconcile` | AC-4, AC-8 |
| `min_success` join (FR-1073) | 0.9, the tolerance for LLM misreads | AC-4 |
| `_map_verdict` (FR-1073) | coverage line in the report | AC-6 |
| `_map_index` ordering (FR-944) | table row order | AC-6 |
| `max_concurrency` (FR-984/FR-1085) | `config.max_concurrency: 8` in the graph | AC-11 |

**Not shown in the real run:**
- **Tolerated failure (`on_error: skip` on the sub-node).** It would turn
  misreads into tolerated failures, so `min_success` would never fire.
  See Q-4.
- **`on_overflow: truncate`.** The demo claims full coverage of the
  corpus (A5).
- **Map-to-map chaining.** There is only one fan-out.
- **`flatten_output` (FR-052).** The report reads `summary` from each
  collected item as it is.

Each of these four is covered only by the existing focused demos. These
are known gaps against the intent. They are listed so the claim can be
checked; they do not narrow it.

### Map version (decided in Python)

The map version describes which keys a node **declares in YAML**. It is
not the runtime contract. Since FR-1073, every map runs under the strict
result contract, including maps that declare none of the new keys. The
report states this in its header. `reconcile` computes the version from
its own parse, so the LLM never states it:

| Version | Rule (checked in this order) | Source |
|---------|------------------------------|--------|
| `overflow` | declares `on_overflow` | FR-939 |
| `result-contract` | declares `failures` or `min_success` | FR-1073 |
| `timeout` | declares `timeout` | FR-069 |
| `capped` | declares `max_items` | map cap |
| `core` | only `over`/`as`/`node`/`collect` | original |

A graph's version is the highest version among its map nodes. The report
also lists the exact declared keys, so the version only shortens the
information and hides nothing.

### Graph sketch (illustrative; the adapter produces the artifact)

```yaml
name: meta-map
state:
  scan_roots: list        # default ["examples", "graphs"]
  poison: list            # default: the three paths above; visible in YAML, not hidden in Python
  output_path: str        # default outputs/meta_map/report.md
config:
  max_concurrency: 8
defaults:
  provider: inception
  model: mercury-2.5      # operator decision 2026-09-27: map and reduce
  on_overflow: error      # FR-939: a corpus above the cap raises before dispatch

nodes:
  discover:
    type: python
    tool: discover_map_graphs         # selection only; returns list[str] of paths
    state_key: paths

  poison_the_source:
    type: python
    tool: poison_the_source           # paths + state.poison, order kept
    state_key: paths

  summarize:
    type: map
    over: "{state.paths}"
    as: path
    max_items: 100                    # above the cap → ValueError, not silent truncation
    on_overflow: error
    timeout: 120
    min_success: 0.9                  # FR-1073: join raises MapCompletenessError below 90 %
    failures: summary_failures        # typed MapFailure records; poisoned paths land here
    node:
      type: subgraph
      graph: subgraphs/summarize_one.yaml
      input_mapping:                  # invoke mode passes nothing unless mapped
        path: path
      output_mapping:
        summary: graph_record
      state_key: summary
    collect: summaries

  reduce:
    type: llm
    prompt: reduce_summaries          # inputs: summaries + python-computed counts
    state_key: overall

  render:
    type: python
    tool: render_report               # rows = summaries; failures = summary_failures, path via state.paths[index]
    state_key: report_path
```

```yaml
# subgraphs/summarize_one.yaml
state:
  path: str
  source: object        # SourceText {path, text}
  claim: object         # MapClaim {map_nodes, intent, map_role}
  graph_record: object  # GraphRecord
nodes:
  read_source: {type: python, tool: read_source, state_key: source}
  describe:    {type: llm, prompt: describe_graph, state_key: claim}
  reconcile:   {type: python, tool: reconcile_claim, state_key: graph_record}
edges:
  - {from: START, to: read_source}
  - {from: read_source, to: describe}
  - {from: describe, to: reconcile}
  - {from: reconcile, to: END}
```

`render` also reads `_map_verdict.summarize` (dispatched / succeeded /
tolerated / failed) and prints it at the top of the report. This is the
coverage header that FR-985 asked for, built from the FR-1073 verdict,
so no new mechanism is needed.

### Report shape

```markdown
# Map usage in YAMLGraph — <git sha>, <date>
Coverage: <dispatched> dispatched · <s> succeeded · 0 tolerated · <f> failed (min_success 0.9 → <required>, met|unmet)
Map version = declared YAML keys; runtime is FR-1073 strict for all maps.

| Path | Map nodes | Sub-node | Version | Declared keys | Intent |
|------|-----------|----------|---------|---------------|--------|
| examples/demos/map-timeout/graph.yaml | process | python | timeout | over, as, node, collect, timeout | … |

## Summary
<reduced text>

## Failures
| Index | Path | Error type | Detail (`MapFailure.message`) |
| <i> | examples/demos/hello/graph.yaml | ClaimMismatchError | claimed [greet], parsed [] |
| <i> | feature-requests/FR-1113-meta-map-demo.md | ClaimMismatchError | claimed [summarize], parsed [] |
| <i> | yamlgraph/compile/map_compiler.py | <LLM error type> | <provider/schema error; no validated claim> |
```

### Files

- `examples/demos/meta_map/graph.yaml`,
  `subgraphs/summarize_one.yaml`, `prompts/describe_graph.yaml`,
  `prompts/reduce_summaries.yaml` — authored only through
  `scripts/author.sh` (graph-authoring doctrine, FR-767).
- `examples/demos/meta_map/tools.py` — `discover_map_graphs`,
  `poison_the_source`, `read_source`, `reconcile_claim`,
  `classify_map_version`, `reduce_inputs`, `render_report`. Pydantic `SourceText`,
  `MapClaim` (the LLM's inline schema, mirrored) and `GraphRecord`
  models; `ClaimMismatchError`. The directory name uses snake_case so
  the module can be imported.
- `examples/demos/meta_map/README.md`, `demo-output.log` (a run of this
  graph).
- `tests/unit/test_fr1113_meta_map.py`. The repository has no
  `tests/unit/examples/` directory; demo tests are flat, as in
  `tests/unit/test_diary_index.py`.
- `capabilities/CAP-286-meta-map-demo.yaml`, REQ-YG-703 in
  `ARCHITECTURE.md`.
- No changes under `yamlgraph/`.

## Acceptance Criteria

- [x] AC-1: `discover_map_graphs` returns the path of every graph with
  at least one `type: map` node under the scan roots, and no other paths.
  Unit test on a fixture tree with a graph that has a map, a graph
  without one, and a non-graph YAML file. A malformed YAML file raises
  an error naming its path; it is not skipped silently (Commandment 6).
- [x] AC-1b: `poison_the_source` returns the discovered paths followed
  by `state.poison` in declared order, and raises if a poison path does
  not exist. `read_source` returns the raw text byte-for-byte for a
  `.yaml`, a `.md` and a `.py` file, and its output has no field that
  classifies the content: the LLM receives the data unjudged. A test
  asserts the `SourceText` schema is exactly `{path, text}`.
- [x] AC-1c: `reconcile_claim` accepts a correct claim for a map graph.
  It raises `ClaimMismatchError`, naming the claimed and the parsed
  values, for a missing map node, an invented map node, and any claim
  about a non-map graph, a `.md` file or a `.py` file, including an
  empty `map_nodes`. The parse it grades against is the same function
  `discover_map_graphs` uses, so selection and grading cannot disagree.
  The `describe` schema has no field that lets the LLM decline.
- [x] AC-2: `classify_map_version` returns the table's version for each
  rule. One parametrized test per row, plus a precedence test: a node
  that declares both `on_overflow` and `timeout` gets `overflow`.
- [x] AC-3: On the real repository, the set of paths returned by
  `discover_map_graphs` equals the set produced by an independent,
  test-local YAML walk of `examples/` and `graphs/`. The assertion
  compares sets of paths, not counts, and has no fixed population
  number.
- [x] AC-4: The graph declares `max_items`, `on_overflow: error`,
  `timeout`, `min_success`, `failures`, and a subgraph sub-node. A unit
  test builds the graph over a fixture corpus plus the three poison
  paths. The stub LLM invents a map node for `hello`, returns an empty
  list for the FR, raises for `map_compiler.py`, and answers the real
  graphs correctly. It asserts: all three poisoned branches are in
  `summary_failures` (two `ClaimMismatchError`, one carrying the stub's
  error type) and none are in `summaries`; `_map_verdict.summarize`
  counts three failures, not tolerated, with `met: true`; `errors` holds
  exactly three `PipelineError`s. A second stub that also misreads
  enough real graphs to push accepted items below 90 % raises
  `MapCompletenessError`.
- [x] AC-5: With a fixture above `max_items`, the run raises before any
  branch runs (FR-939 `error`).
- [x] AC-5b: A fixture run proves the child subgraph receives the
  dispatched `path` through `input_mapping`, and that each `summaries`
  entry holds one `GraphRecord` through `output_mapping`. It must be
  neither empty nor the child's whole state.
- [x] AC-6: `render_report` accounts for every dispatch index exactly
  once across the success and failure tables. It orders success rows by
  `_map_index`, resolves failed paths as `state.paths[MapFailure.index]`,
  writes `MapFailure.message` verbatim as the detail, lists declared keys
  verbatim, and builds the coverage line only from
  `_map_verdict.summarize`. The fixtures include a failed real graph as
  well as the poison paths.
- [x] AC-7: `yamlgraph graph lint examples/demos/meta_map/graph.yaml`
  passes.
- [x] AC-8: A real smoke run over the repository writes
  `outputs/meta_map/report.md` and exits 3 (FR-1097). The Failures
  section contains all three poisoned paths, and the committed
  `demo-output.log` comes from that run. For each poisoned path, the FR
  quotes verbatim what the LLM said (or its error). It also records
  three raw claims for real graphs, each with one concrete detail
  (`read_raw_output_first`), before any count is quoted in the README.
- [x] AC-9: `tmp/draft-authoring-report.md` from `scripts/author.sh`
  is cited in this FR as the authoring evidence.
- [x] AC-10: Tests carry `@pytest.mark.req(...)`, and a REQ ID and
  capability entry are added (or reused if one exists).
  `python scripts/req_coverage.py --strict` passes.
- [x] AC-11: A graph-load test asserts that the loaded `summarize`
  config declares `timeout: 120` and that the run config resolves
  `max_concurrency` to 8. This is a declaration witness: the framework's
  timeout behavior is already tested by `map-timeout`. Every row of the
  Coverage matrix names a witness AC that exists.
- [x] AC-12: A `feat` changelog fragment, a README link from
  `reference/graph-yaml.md` → map section ("full example"), and a diary
  entry with a `Seed:`.

## Implementation Status (2026-09-27)

Commits: `81c7fe06` plan + brief · `c8560676` RED witnesses + CAP-286 /
REQ-YG-703 · `a6e9a1f2` RED poison-once + repair brief · `e192924e` RED
smoke-found reconcile defects · `c6ab3737` GREEN (demo, proofs, fragment).
42 tests in `tests/unit/test_fr1113_meta_map.py` pass. The full unit suite
passed in the GREEN commit's pre-commit run.

**Authoring evidence (AC-9).** Two `scripts/author.sh` runs, both reports
kept locally:

- Round 1, brief `fr-1113-meta-map-demo-brief.md`
  (`tmp/authoring-report-1113-round1.md`): authored `graph.yaml`,
  `poison.yaml`, `subgraphs/summarize_one.yaml` and both prompts. This
  report lists every new governed path, so it is the one restored as
  `tmp/draft-authoring-report.md` for the FR-767 commit check.
- Repair, brief `fr-1113-meta-map-demo-repair-brief.md`
  (`tmp/authoring-report-1113-repair.md`): removed `init_poison`; lint
  passed and 39/39 tests passed.

`tools.py` is not a governed artifact and was written in the enforcing
session.

**Real run (AC-8).** `inception/mercury-2.5`, exit 3: 55 dispatched ·
52 succeeded · 0 tolerated · 3 failed, `min_success` 0.9 met
(ceil(0.9 × 55) = 50). The full log is
`examples/demos/meta_map/proofs/poisoned-run/run-evidence.txt`.
Poisoned paths, verbatim `MapFailure.message`:

- `examples/demos/hello/graph.yaml: claimed [], parsed [] (source has no map nodes)`.
  The model told the truth; the branch fails anyway because the source
  is not a map graph.
- `feature-requests/FR-1113-meta-map-demo.md: claimed ['summarize'], parsed [] (source has no map nodes)`.
  The only poison that fooled the model, through this FR's own
  illustrative graph sketch.
- `yamlgraph/compile/map_compiler.py: claimed [], parsed [] (source has no map nodes)`.

Raw claims for three real graphs:

- `examples/demos/chatterbox/graph.yaml`, `generate`: "demonstrates
  multilingual text-to-speech by generating translations for multiple
  languages and synthesizing audio for each". Its sub-node has no
  `type:`. The first run reported this as `unknown`, which led to a fix
  (see below).
- `examples/demos/map-timeout/graph.yaml`, `process`: python sub-node,
  version `result-contract`, because it declares `min_success` alongside
  `timeout`.
- `examples/demos/meta_map/graph.yaml`, `summarize`: the demo counted
  itself. Subgraph sub-node, version `overflow`: "summarizes each via a
  subgraph, and renders a report including poison failure checks".

**Deviations.**

1. `init_poison` removed by a repair brief. The round-1 author duplicated
   the poison list in a passthrough node so that a raw `invoke()` would
   see it. Root cause: the test harness did not merge `data_files` the
   way the CLI does (`graph_run_helpers._build_run_config`). The harness
   was fixed at the callsite, a RED test was added
   (`test_poison_declared_once_in_data_file`), and the graph was
   repaired through the adapter.
2. Two defects found by the smoke, both fixed test-first (`e192924e`):
   - An untyped map sub-node was recorded as `unknown`, but the runtime
     default is `llm` (`map_compiler.py`, `sub_node_config.get("type", "llm")`).
   - A non-map mismatch read `claimed [], parsed []`, which looks like
     agreement. The message now appends `(source has no map nodes)`.
3. `demo-output.log` holds `yamlgraph graph validate` output for this
   graph, not the poisoned run. `scripts/demo_log_semantics.sh` treats
   any `[ERROR]` line as fatal, and this demo emits three by design. The
   gate was not widened (it is a same-session enforcement edit). The
   approach follows `map-timeout`, and the real run goes under
   `proofs/poisoned-run/` as in `corpus_census/proofs/`. AC-8's "committed
   `demo-output.log` comes from that run" is met by the proofs file
   instead.
4. `prepare_reduce` (`reduce_inputs`) was added between map and reduce,
   so the reduce prompt gets counts computed from `_map_verdict` (R-5),
   not counts the LLM derives.
5. Tests live at `tests/unit/test_fr1113_meta_map.py`.
6. The dispatch count is 55, not a fixed number (AC-3): 52 map graphs
   (including meta_map itself) plus 3 poison paths.

## Alternatives Considered

| # | Alternative | Disposition |
|---|-------------|-------------|
| A1 | Add map syntax to `pipeline_audit` | **Rejected.** In that graph an agent chooses when to call `scan_graphs_tool`, so discovery is not deterministic, and it would still have no map node. It would be a demo that does not use the feature it demonstrates. |
| A2 | Run `corpus_census` with a new graph-YAML adapter (FR-1033 style) | **Rejected (Q-1 = a).** It reuses tested census code. But census scores items against a brief, and this demo needs structured extraction plus a Python-computed version. It would also hide the map node inside machinery that already exists, which defeats the point of a demo. |
| A3 | Let the LLM infer the map version from YAML text | **Rejected.** The version is a fixed function of the keys, and LLM output is not reliable for it (`plausible_wrong_answer`). Normalize at the boundary: the LLM claims only what a parse can check (which map nodes), `reconcile` checks the claim, and the version comes from the parse. |
| A4 | Python script only, no LLM | **Rejected.** A script can produce the inventory but cannot state the intent of each graph or write a summary, and those are what was requested. |
| A5 | Sample with `on_overflow: truncate` | **Rejected.** The demo claims to cover the whole corpus. Truncating would silently drop graphs, so the default `error` is correct here. |
| A6 | Also scan the graphs' Python consumers for reads of `failures` vs `_error` | **Out of scope (Q-2 = a).** Useful for migrations, but it is a second analysis and not required by the request. |
| A7 | A Python `inspect` step that validates the path and raises before the LLM runs | **Rejected (operator review, 2026-09-27).** It grades its own exam: the demo poisons the input and then its own guard catches exactly that poison. The failures would be staged, the LLM would never see bad data, and the real risk would go untested: an LLM given bad data returning a plausible wrong answer. The branch reads the file plainly and grades the LLM's claim afterwards. |

## Related

- [reference/graph-yaml.md — `type: map`](../reference/graph-yaml.md)
- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md)
- `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/map_contract.py`,
  `yamlgraph/models/map_results.py` (read-only dependencies)

### Questions for the human

Q-1, Q-2 and Q-4 are resolved to option (a) at `enforce` (see Status).

- **Q-1 (A2):** (a) standalone demo *(recommended: the purpose is to show
  the map node, and census adapters would hide it)*; (b) census adapter.
- **Q-2 (A6):** (a) leave out *(recommended: keeps scope to the request)*;
  (b) add a "reads `failures`" column taken from a scan of the graph's
  `tools*.py`.
- **Q-4 tolerated failures:** (a) do not show them in the real run
  *(recommended: `on_error: skip` on the sub-node would make misreads
  tolerated and `min_success` would never fire)*; (b) add a second,
  small map that sets `on_error: skip` over the same poison, so the
  report can compare tolerated and failed side by side.
- **Q-3 map model: answered 2026-09-27.** `provider: inception`,
  `model: mercury-2.5` for both map and reduce, pinned in the graph
  `defaults`.
