# Feature Request: `graph run` refuses `--var` and `--var-file` keys the graph's state cannot hold

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1084-reject-undeclared-cli-vars.judgement.md)); authority gated on folding the required revisions. No implementation authority yet.
**Human decision (2026-09-25, operator):** suggested default accepted — graph `variables:` keys missing from the schema are out of scope here and get their own FR.
**Effort:** 1 day
**Requested:** 2026-09-25
**First consumer / first event:** the next
`yamlgraph graph run examples/demos/innovation_matrix/pipeline.yaml --var domain=@brief.md`.
On 2026-09-24 `domain` never reached state, `{state.domain}` resolved to
`None`, and all 25 cells were built on domain-free dimensions
([docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.1).
**Research:** FR-890 research route **skipped by operator decision
(2026-09-25)**: "refile. skip research — document as skipped". Substitute:
the in-body Alternatives Considered below (six solution classes, one chosen,
one preserved dissent, each dispositioned, plus an `is_this_a_graph` answer),
in the form FR-1076's judgement accepted; plus a runtime probe run on
2026-09-25 against this worktree (Problem, finding 3) and
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.1, §2 D5, §7 C.
**Prior art:**
[FR-1067](FR-1067-reject-undeclared-cli-vars.md) (REJECTED). Same fix,
refused for a missing research record. This refile answers each judgement
point; see "Answers to the FR-1067 judgement" below.
[FR-677](FR-677-verification-first-class-dsl.md) (Done). Its "E-level lint
findings block execution" line is scoped to `graph run --gate`
([FR-677#L77-L84](FR-677-verification-first-class-dsl.md#L77-L84)). FR-677
made the gate opt-in on purpose ("Lint-first, opt-in. `--gate` (default
off)", [FR-677#L224](FR-677-verification-first-class-dsl.md#L224)). The code
matches: the gate runs only when the flag is set
([graph_commands.py#L128-L130](../yamlgraph/cli/graph_commands.py#L128-L130)).
So there is no contradiction to resolve. FR-677 blocks on static findings
when asked. This FR refuses bad runtime input always. It does not change the
gate.
REQ-YG-069 (E007, [ARCHITECTURE.md#L786](../ARCHITECTURE.md#L786)). The
static counterpart: `{state.X}` refers to an undeclared field
([checks_semantic.py#L176-L194](../yamlgraph/linter/checks_semantic.py#L176-L194)).
[FR-269](FR-269-cli-inter-run-state-chaining.md) (Implemented).
`--import-state` loads a prior run's full state, often from a different
graph ([FR-269#L71-L80](FR-269-cli-inter-run-state-chaining.md#L71-L80)).
[FR-688](FR-688-cli-variables-injection.md) (Closed). Graph `variables:` are
merged into the initial state as the lowest layer.
[FR-892](FR-892-corpus-census-pipeline-injected-adapters.md). Precedent for
refusing bad CLI input before any token is spent
([graph_commands.py#L156](../yamlgraph/cli/graph_commands.py#L156)).
[FR-1088](FR-1088-innovation-matrix-repair.md) (Proposed, refile of FR-1070).
Declares `domain` in `pipeline.yaml`; the first consumer's run passes this
check once it lands.

## Summary

Before invoking the graph, `graph run` compares the `--var` and `--var-file`
keys with the keys of the graph's state schema. If any key is unknown, it
exits 1, names the key, and lists the keys the graph accepts. No LLM call is
made.

## Value Statement

A graph author who types a wrong or undeclared input name learns it in one
second, with the accepted names. Today the run finishes on `None` and looks
plausible.

## Problem

1. The CLI merges `--var-file` and `--var` over imported state
   ([graph_commands.py#L132-L147](../yamlgraph/cli/graph_commands.py#L132-L147))
   and passes the result on without a check.
2. The state schema is a `TypedDict` built from base fields, common input
   fields, `state:`, `data_files`, and node-derived keys such as `state_key`
   and map `collect`
   ([state_builder.py#L174-L213](../yamlgraph/models/state_builder.py#L174-L213),
   [#L64-L91](../yamlgraph/models/state_builder.py#L64-L91)).
3. LangGraph drops input keys that are not in that schema. Probe, 2026-09-25,
   on a throwaway graph with `state: {declared: str}`, a node with
   `state_key: inferred_sk`, and graph `variables: {gv: …}`:
   - `app.input_channels` is the single channel `__start__`. FR-1067's
     "compiled input channels" named the wrong source.
   - `app.get_input_jsonschema()["properties"]` equals the keys of the
     built `TypedDict`. It contains `declared`, `inferred_sk`, `thread_id`,
     `topic`; not `gv`, not `domain`.
   - Input `{declared, gv, domain}`: `invoke`, `ainvoke` and
     `astream(stream_mode="values")` all return `declared` only. `domain`
     and `gv` are dropped silently.
4. Finding outside this FR's fix: graph `variables:` keys are merged into the
   initial state
   ([graph_run_helpers.py#L129-L131](../yamlgraph/cli/graph_run_helpers.py#L129-L131)),
   but `build_state_class` does not add them to the schema. A `variables:`
   key that is not also declared elsewhere is dropped (probe: `gv`). See
   "Human decision needed".

## Ideal Result

Every key a user passes with `--var` or `--var-file` either reaches state or
the run is refused before any token is spent, with a message naming the
accepted keys. The same holds in sync, `--async` and `--stream` modes.

## Proposed Solution

1. **Accepted-key source.** The keys of the state schema the compiled graph
   uses: `app.get_input_jsonschema()["properties"]`, which the probe showed
   equals the `build_state_class` keys. No second list is maintained.
2. **Where.** In `cmd_graph_run`, after `graph.compile(...)`
   ([graph_commands.py#L175](../yamlgraph/cli/graph_commands.py#L175)) and
   before `_build_run_config`
   ([#L178-L180](../yamlgraph/cli/graph_commands.py#L178-L180)). This is
   before the stream branch (#L183-L185) and the sync/async invoke, so one
   check covers all three modes.
3. **Which keys.** `file_vars` and `cli_vars` only. Not `imported_state`
   (FR-269: a prior run's full state, often from another graph). Not graph
   `variables:` or `data_files` (authored in the graph, not user input).
4. **Message.** To `error_stream`
   ([#L118](../yamlgraph/cli/graph_commands.py#L118)), then exit 1:
   `❌ --var 'domain' is not a state key of pipeline.yaml; declare it under state: or use one of: …`.
   The list omits names that start with `_`.
5. **Census of documented invocations.** A deterministic extractor collects
   every `yamlgraph graph run <path> … --var k=…` / `--var-file` from
   `README.md`, `reference/**/*.md`, `examples/**/README.md` and
   `examples/demos/demo.sh`, joining `\` line continuations. It compiles each
   graph and checks each key. Size today: about 251 lines mention
   `graph run` and about 306 mention `--var` in that scope (grep count,
   2026-09-25; the extractor gives the exact number). Each failure is either
   fixed in the same PR, or listed in a committed exclusion file with a
   reason and the FR number of a separately filed defect. No blanket-pass
   claim.

## Acceptance Criteria

- [ ] AC-01 (RED): fixture graph with `state: {declared: str}`, a node with
  `state_key: inferred_sk`, graph `variables: {gv_declared: …}` where
  `gv_declared` is also in `state:`, and an LLM node whose client is mocked.
  `graph run --var unknown=x` exits 1, prints the message naming `unknown`,
  and the mock records zero calls.
- [ ] AC-02: the same unknown key in a `--var-file` gives the same exit and
  message.
- [ ] AC-03: `--var declared=a --var inferred_sk=b --var gv_declared=c`
  passes the check, and the final state holds all three values. Run in sync,
  `--async` and `--stream` modes.
- [ ] AC-04: a witness test shows the accepted-key set equals the keys kept by
  `invoke` and `ainvoke`: every schema key passed in is present in the
  result, and a non-schema key is absent.
- [ ] AC-05: `--import-state` with a JSON holding `declared` and a foreign key
  `other_graph_key` runs without error. `declared` reaches state;
  `other_graph_key` is dropped as today (FR-269 behaviour kept).
- [ ] AC-06: `--var gv_only=x`, where `gv_only` is a graph `variables:` key
  that is not a schema key, is refused. The message says it is not a state
  key.
- [ ] AC-07: census test over the corpus in Proposed Solution item 5. Every
  extracted invocation passes, or appears in the committed exclusion file with
  a reason and a filed defect FR number. The extracted list is committed with
  the test.
- [ ] AC-08: once `innovation_matrix/pipeline.yaml` declares `domain`
  (FR-1088), `--var domain=x` passes the check. Before that, it is refused.
- [ ] AC-09: new REQ in a capability file, tests tagged,
  `python scripts/req_coverage.py --strict` passes, changelog fragment, FR
  implementation record, diary entry.

## Answers to the FR-1067 judgement

| Judgement point | Answer in this FR |
|---|---|
| R-1: four-to-six-class disposition, precedent, dissent, `is_this_a_graph` | Alternatives Considered: six classes, cited precedent, dissent kept (class 2), graph-fit answer. |
| R-1: disposition FR-677's E-level claim in the refile itself | Prior art: FR-677's claim is scoped to `--gate` and opt-in by its own decision (#L224); code agrees (#L128-L130). |
| R-2: prove the accepted-key source for sync and async | Problem finding 3 (probe); AC-03 and AC-04 make it a test. Source changed from "input channels" to the input schema. |
| R-2: fixture with `state:`, inferred keys, `variables`, `--var-file`, unknown key | AC-01, AC-02, AC-03, AC-06. |
| R-2: imported state exempt only if its fields are kept | AC-05. |
| R-2 / AC-03: no "listed as defects" beside a blanket pass | Proposed Solution item 5 and AC-07: fix, or exclusion with reason and filed defect FR. |
| C-1: no implementation under FR-1067 | This FR is the new vehicle; FR-1067 stays Rejected. |
| C-2: no global missing-expression error | Out of scope; Alternatives class 6 rejected. |

## Alternatives Considered

Solution classes (chosen: 1):

1. **CLI boundary check against the compiled state schema.** Chosen. The CLI
   is where user input enters (`the_one_law`). The schema is the truth
   LangGraph uses to drop keys, so the check cannot drift from it. Precedent:
   FR-892 refuses bad slot bindings at the same boundary before any token.
2. **Strict state at the engine** (reject unknown keys at every invoke, for
   example a Pydantic state with `extra="forbid"`). **Preserved dissent.** It
   covers every caller: CLI, Python API, graph tools, subgraphs. It loses
   here because each internal caller that passes a wider dict would first
   need an audit, and this FR has one named consumer, the CLI. If a second
   caller hits D5, this class is the next step.
3. **Turn `--gate` on by default** (FR-677 foresaw a flip "once examples are
   clean", [FR-677#L83](FR-677-verification-first-class-dsl.md#L83)).
   Rejected: E007 checks `{state.X}` references, not CLI keys. A typo such as
   `--var domian=x` passes lint when `domain` is declared, and is still
   dropped. It also changes every run on any error-level finding.
4. **Warn instead of refuse.** Rejected: a warning in a long log is how D5
   went unnoticed (Commandment 6).
5. **Accept every CLI key by adding it to the schema at run time.** Rejected:
   the typo reaches state under the wrong name, and `{state.domain}` is still
   `None`. It hides the error instead of reporting it.
6. **Make a missing `{state.X}` raise at expression time.** Rejected: FR-1067
   judgement C-2 forbids it under this FR, and plan §7 C notes a much larger
   blast radius that needs its own census.

`is_this_a_graph`: no. The check is set membership at the input boundary.
The census of documented invocations is a deterministic parse of shell lines,
not a model judgement.

## Human decision needed

- **Graph `variables:` keys that are not schema keys are dropped** (Problem
  finding 4). FR-688 meant them to reach state. Suggested default: not fixed
  here, because they are graph-authored, not CLI input. File it as its own FR
  (for example: `build_state_class` adds `variables:` keys as `Any` fields,
  or `graph lint` reports them). This FR's fixtures use only `variables:`
  keys that are also declared, so they do not depend on the choice.

## Out of scope

Expression strictness for missing `{state.X}` (C-2). Changing the `--gate`
default. Strict state for non-CLI callers (class 2). Graph `variables:` keys
missing from the schema (Human decision needed). `graph bench`, which merges
vars the same way
([bench_commands.py#L284-L286](../yamlgraph/cli/bench_commands.py#L284-L286)).
Checking `--import-state` keys.

## Related

- Refile of: [FR-1067](FR-1067-reject-undeclared-cli-vars.md)
- Composes with: [FR-1088](FR-1088-innovation-matrix-repair.md), [FR-677](FR-677-verification-first-class-dsl.md), [FR-269](FR-269-cli-inter-run-state-chaining.md), [FR-688](FR-688-cli-variables-injection.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D5, §7 C
