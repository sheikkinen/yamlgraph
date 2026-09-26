# Feature Request: `graph run` refuses `--var` and `--var-file` keys the graph's state cannot hold

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1084-reject-undeclared-cli-vars.judgement.md)); R-1–R-3 folded 2026-09-26. Authority active (2026-09-26): C-1 human review recorded — operator instruction 'proceed with all fr changes' (2026-09-26).
**Human decision (2026-09-25, operator):** suggested default accepted — graph `variables:` keys missing from the schema are out of scope here and are filed as [FR-1091](FR-1091-graph-variables-reach-state.md) (Parked). See "Human decisions".
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
REQ-YG-069 (E007, [ARCHITECTURE.md#L788](../ARCHITECTURE.md#L788)). The
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
Declares `domain` in `pipeline.yaml`. FR-1084 neither waits for FR-1088 nor
edits its graph; the census records the innovation-matrix invocation as
`PASS` or as `EXCLUDED` with FR-1088 (AC-10).

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
   [#L65-L92](../yamlgraph/models/state_builder.py#L65-L92)).
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
   key that is not also declared elsewhere is dropped (probe: `gv`). Filed
   as [FR-1091](FR-1091-graph-variables-reach-state.md) (Parked); see
   "Human decisions".

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
4. **Algorithm and message.**
   1. Take the union of the keys in `file_vars` and `cli_vars`.
   2. Subtract the property names of `app.get_input_jsonschema()`.
   3. If anything is left, sort it lexicographically and fail once, naming
      every unknown key.
   4. The accepted-key list in the message is sorted lexicographically and
      omits names that start with `_`. This hides them from display only;
      they are still accepted.
   5. If the schema cannot be read or has no `properties`, the run fails
      loudly through the existing CLI error path. There is no fallback to a
      separately built field set.

   Frozen message, for both sources:
   `❌ Unknown --var/--var-file state key(s) for <graph file name>: <unknown keys>; accepted keys: <accepted keys>`,
   for example
   `❌ Unknown --var/--var-file state key(s) for pipeline.yaml: domain, typo; accepted keys: declared, inferred_sk`.
   Lists are comma-separated. The message goes to `error_stream`
   ([#L118](../yamlgraph/cli/graph_commands.py#L118)): stdout in human
   mode; stderr in `--json` mode, where stdout stays empty. Exit code 1.
5. **Census of documented invocations.** A deterministic extractor collects
   every `yamlgraph graph run` invocation in `README.md`,
   `reference/**/*.md`, `examples/**/README.md` and `examples/demos/demo.sh`.
   Size today: about 251 lines mention `graph run` and about 306 mention
   `--var` in that scope (grep count, 2026-09-25; the extractor gives the
   exact number).
   - **Row shape.** One row per (invocation, key): source file, line of the
     `yamlgraph graph run` token, graph path, source kind (`--var` or
     `--var-file`), key, and `PASS` or `EXCLUDED`.
   - **Line continuations.** A trailing `\` joins the next line before
     parsing.
   - **Repeated `--var`.** A key given twice in one invocation is one row.
     Only keys are checked, never values.
   - **`--var-file`.** The path is resolved from the repository root. If the
     file exists, its keys are read with the CLI's own `load_var_file`, one
     row per key. If it does not exist: one row with key `-`, `EXCLUDED`,
     reason `missing-var-file`.
   - **Placeholders and shell variables.** A graph path or key containing
     `<`, `>`, `...` or `…` is `EXCLUDED`, reason `placeholder`; one
     containing `$` is `EXCLUDED`, reason `shell-variable`.
   - **Unresolvable graph.** A graph path that does not exist is `EXCLUDED`,
     reason `unresolvable-graph`.
   - The four reasons above mark unresolvable rows; they carry no FR number.
     Every other `EXCLUDED` row (an unknown key, or a graph that fails to load
     or compile) records a reason and the number of a filed FR.
   - **Repairs.** The only repair allowed under this FR is a documentation
     key typo where the compiled schema makes the intended key unambiguous;
     the row then becomes `PASS`. Any finding that needs a graph, prompt,
     runtime or semantic change is excluded and filed separately.
   - The extracted rows and the exclusion manifest are committed under
     `tests/fixtures/fr1084/`; the test regenerates both and compares them
     byte-for-byte, so stale evidence fails.

## Acceptance Criteria

- [ ] AC-01 (RED): a temporary fixture graph with `state: {declared: str}`,
  a node with `state_key: inferred_sk`, graph `variables: {gv_declared: …}`
  where `gv_declared` is also in `state:`, and a mocked LLM client exits 1
  for `--var unknown=x`; the exact diagnostic names `unknown`, lists the
  sorted visible accepted keys, and the mock records zero calls.
- [ ] AC-02: unknown keys split across `--var-file` and `--var` are unioned,
  deduplicated, sorted, reported in one diagnostic, and exit 1 before
  `_build_run_config` or graph invocation.
- [ ] AC-03: in human mode the frozen diagnostic is written to the existing
  `error_stream`; with `--json`, stdout is empty and stderr contains exactly
  the diagnostic.
- [ ] AC-04: `--var declared=a --var inferred_sk=b --var gv_declared=c`
  passes validation and the final state contains all three values in
  synchronous, `--async` and `--stream` runs.
- [ ] AC-05: on the same fixture, `app.get_input_jsonschema()["properties"]`
  equals the keys retained when all schema keys plus one non-schema key are
  supplied through `invoke`, `ainvoke` and `astream(stream_mode="values")`;
  the non-schema key is absent in every mode.
- [ ] AC-06: `--import-state` containing `declared` and `other_graph_key` is
  not validated as user variables; the run succeeds, `declared` reaches
  state, and the foreign key is absent from the result.
- [ ] AC-07: `--var gv_only=x`, where `gv_only` exists only under graph
  `variables:`, exits 1 as an unknown state key; an underscore-prefixed
  schema key remains accepted but is omitted from the displayed accepted-key
  list.
- [ ] AC-08: the deterministic census covers `README.md`,
  `reference/**/*.md`, `examples/**/README.md` and `examples/demos/demo.sh`,
  joins shell continuations, emits the frozen row shape, and exactly matches
  the committed extracted list and exclusion manifest.
- [ ] AC-09: every resolvable census row is `PASS` or has a reasoned
  `EXCLUDED` record with a filed FR number; only an unambiguous documentation
  key typo may be repaired under this FR.
- [ ] AC-10: the innovation-matrix `--var domain=...` row is `PASS` if the
  checkout's compiled schema contains `domain`; otherwise it is `EXCLUDED`
  with FR-1088 and `domain` recorded as the unknown key. No innovation-matrix
  artifact changes under FR-1084.
- [ ] AC-11: a new capability/REQ entry governs CLI variable validation;
  every new or changed test function carries its requirement marker;
  `python scripts/req_coverage.py --strict` passes; and the changelog
  fragment, FR implementation record and diary entry are present.

## Scope (frozen by judgement)

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/cli/graph_commands.py`: one compiled-input-schema validator called after `app = graph.compile(...)` and before `_build_run_config` |
| D-2 | Focused FR-1084 CLI tests using temporary graph and variable-file fixtures for unknown, accepted, imported, graph-variable, sync, async, stream and JSON-output behaviour |
| D-3 | Deterministic documented-invocation census test, committed extracted list and committed exclusion manifest under `tests/fixtures/fr1084/` |
| D-4 | Capability/REQ traceability, changelog fragment, FR implementation record and diary distillation |

Not authorized: changes to graph or prompt artifacts, including
`innovation_matrix`; global strict-state behaviour; expression strictness;
the E007 implementation or `--gate` default; validation of
`--import-state`; adding graph `variables:` to the state schema;
`graph bench`; LangGraph patches, shims or a duplicated accepted-key
registry; repairs to census findings beyond an unambiguous
documentation-only key typo.

## Conditions for enforcement

Gates C-1 to C-7 in the
[judgement](FR-1084-reject-undeclared-cli-vars.judgement.md#conditions-for-enforcement)
apply: human review (C-1, recorded below), the compiled input schema as the
only key source (C-2), validating only `--var`/`--var-file` at the stated
point (C-3), exit before any invocation or LLM call (C-4), census cannot
widen scope (C-5), no dependency on FR-1088 (C-6), RED before GREEN with
strict REQ coverage (C-7).

## Answers to the FR-1067 judgement

| Judgement point | Answer in this FR |
|---|---|
| R-1: four-to-six-class disposition, precedent, dissent, `is_this_a_graph` | Alternatives Considered: six classes, cited precedent, dissent kept (class 2), graph-fit answer. |
| R-1: disposition FR-677's E-level claim in the refile itself | Prior art: FR-677's claim is scoped to `--gate` and opt-in by its own decision (#L224); code agrees (#L128-L130). |
| R-2: prove the accepted-key source for sync and async | Problem finding 3 (probe); AC-04 and AC-05 make it a test. Source changed from "input channels" to the input schema. |
| R-2: fixture with `state:`, inferred keys, `variables`, `--var-file`, unknown key | AC-01, AC-02, AC-04, AC-07. |
| R-2: imported state exempt only if its fields are kept | AC-06. |
| R-2 / AC-03: no "listed as defects" beside a blanket pass | Proposed Solution item 5, AC-08 and AC-09: pass, or exclusion with reason and filed FR. |
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

## Human decisions

- **2026-09-25, operator — graph `variables:` keys that are not schema keys
  are dropped** (Problem finding 4). FR-688 meant them to reach state.
  Decision: not fixed here, because they are graph-authored, not CLI input.
  Filed as [FR-1091](FR-1091-graph-variables-reach-state.md) (Parked). This
  FR's fixtures use only `variables:` keys that are also declared, so they do
  not depend on that FR.
- **2026-09-26, operator — advisory judgement reviewed** (C-1). Instruction:
  "proceed with all fr changes". R-1–R-3 folded the same day.

## Out of scope

Expression strictness for missing `{state.X}` (FR-1067 judgement C-2).
Changing the `--gate` default. Strict state for non-CLI callers (class 2).
Graph `variables:` keys missing from the schema (FR-1091). Any edit to
`innovation_matrix` (FR-1088). `graph bench`, which merges
vars the same way
([bench_commands.py#L284-L286](../yamlgraph/cli/bench_commands.py#L284-L286)).
Checking `--import-state` keys.

## Related

- Refile of: [FR-1067](FR-1067-reject-undeclared-cli-vars.md)
- Composes with: [FR-1088](FR-1088-innovation-matrix-repair.md), [FR-677](FR-677-verification-first-class-dsl.md), [FR-269](FR-269-cli-inter-run-state-chaining.md), [FR-688](FR-688-cli-variables-injection.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D5, §7 C
