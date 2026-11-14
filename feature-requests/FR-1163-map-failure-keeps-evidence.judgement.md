# Judgement: FR-1163 Keep what succeeded and what it cost when a strict map fails

**Route:** scripts/judge.sh (copilot gpt-6.1-sol), draft folded verbatim. Disposition: APPROVED WITH REVISIONS; R-1..R-4 folded into the FR.
**Prior art:** dispositioned in the FR's Prior art line and judged in the rubric below.


**Verdict:** APPROVED WITH REVISIONS — preserving evidence at the existing exception boundary is sound; implementation authority activates only after R-1 through R-4 are folded into the committed FR.

**Reviewed against:** Committed HEAD `0547e227701080b2546f120e801dca90a386716d`, with no staged or working-tree changes when inspected:

- `feature-requests/FR-1163-map-failure-keeps-evidence.md` (complete).
- `feature-requests/FR-1163.research.md` (complete).
- `yamlgraph/models/map_results.py`; `yamlgraph/compile/map_contract.py`; `yamlgraph/compile/cached_map_compiler.py` (complete).
- `yamlgraph/compile/map_compiler.py` (lines 1-310, 395-442 and targeted join/collect/failures references).
- `yamlgraph/cli/graph_commands.py` (lines 1-300 and targeted exception/exit references); `yamlgraph/cli/graph_run_helpers.py` (lines 1-320 and targeted output/exit references).
- `feature-requests/FR-1073-map-result-contract.md` (lines 1-205 and targeted shared-channel, loop, checkpoint and acceptance references); its `.judgement.md` (lines 1-120).
- `feature-requests/FR-1161-cached-map-warm-first.md` (lines 1-140 and targeted contract references); `feature-requests/FR-1097-graph-run-completed-errors-exit-3.md` (lines 1-145 and targeted exit/checkpoint references).
- Targeted precedent excerpts from `feature-requests/027-execution-safety-guards.md`, `feature-requests/FR-231-model-provider-timing-comparison.md`, `feature-requests/FR-1152-thinking-tokens-in-token-usage.md`, `feature-requests/FR-1155-prompt-cache-tokens-in-token-usage.md`, `feature-requests/FR-1160-remove-map-memo-contrib.md`, `feature-requests/FR-1116-map-memo-file-corpus.md`, `feature-requests/FR-1005-research-route-row-failed-demotion.md`, and `feature-requests/FR-962-person-profile-census-authored-prs.md`.
- `.github/copilot-instructions.md` (supplied doctrine and on-disk lines 1-80); `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

No author transcript, working notes, external web content, or uncommitted evidence was consumed. FR-1130 is treated only as the FR's contextual claim, not independently verified incident evidence. This is a draft, not promotion of the governing judgement.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The exception already crosses the relevant boundary; attaching evidence avoids introducing a checkpointer or durable store (`FR-1163:84-108,138-147`). A smaller CLI-only fix cannot recover answers from an uncheckpointed failed invocation. R-2 bounds the exit-path work. |
| Consistency | Keeping the completeness raise and downstream block is consistent with FR-1073 and FR-1097 (`FR-1163:14-18,107-108`; `FR-1097:40-49`). The unspecified collect identity, streaming path, and omitted JSON timing contradict or underdetermine the reporting promise; R-1 through R-3 resolve them. |
| Measurability | AC-01 through AC-06 have concrete exception, stdout and exit assertions (`FR-1163:112-127`). Merely checking a heading or JSON key does not prove retained usage values, and there is no timing witness; R-4 adds discriminating assertions. |
| Feasibility | Results and typed failures are available at fan-in, and both compilers call the shared join (`map_compiler.py:187-214,427-430`; `cached_map_compiler.py:124-130`). The CLI trackers exist before execution (`graph_commands.py:212-215`). The streaming error-event exit and inner timeout exit bypass the proposed outer exception handler (`graph_commands.py:46-66,218-221,261-263`); treating that handler as universal is not workable. |
| Architecture alignment | Compile/model code should carry data and CLI code should format it, using existing typed verdict/failure models and result display (`map_results.py:13-45,55-67`; `graph_run_helpers.py:55-88`). No orchestration graph is needed. Failure serialization must retain those records as objects rather than their reprs. |
| Single responsibility | Retaining partial-map evidence and already-collected execution usage are one failure-reporting concern. Retry policy, persistence, cache scheduling and post-output export-error redesign are independent concerns and remain excluded. |
| Strategic classification | **Framework primitive correction, not a new abstraction.** Existing map execution is used by innovation-matrix synthesis, corpus-census filtering and domain crawling (`FR-1073:9-12,61-79`), and cached maps share its join (`FR-1163:16-17`). Counts-only exceptions do not satisfy the evidence contract. This does not justify another node type or result-storage API. |
| Testability | Real compiled Python-worker graphs can witness the exception and downstream block without provider access (`FR-1163:112-115,126-127`). Controlled usage callbacks can witness reporting. R-4 fixes the zero-call Python-node test and covers actual sync/async propagation instead of only injecting an exception into the CLI. |

The strongest case against this change is that an exception could become an alternate state-export protocol, exposing accumulated results as if they belonged to the failed dispatch while proliferating streaming and JSON machinery. R-1 explicitly labels the existing channel snapshot; R-2 defers streaming partial-result transport. These bounds keep the repair smaller than durable storage or a new execution-result protocol.

The research gate is substantive when the committed record is read together with the FR's dispositions: durable retention, exception-carried evidence, CLI/checkpoint-only reporting and threshold relaxation are distinguished, with explicit reasons for selection or rejection (`FR-1163.research.md:20-26`; `FR-1163:138-151`). AWS is an analogy, not a fifth independent implementation class. The durable-storage disagreement survives in the source rows and is answered by the no-default-checkpointer constraint. The internal rows answer `is_this_a_graph` negatively; the librarian's "Yes" describes Step Functions, not a proposed YAMLGraph artifact.

Prior art is not overturned: FR-1073 keeps the hard join; FR-1097 keeps completed-run exit 3; FR-1161's recorded operator overrule concerns warm-first scheduling, not reporting. FR-1116's durable memo already addresses cross-run retention and is not a reason to add storage here. FR-1160 removes a different memo implementation. FR-1005's persona demotion and FR-962's census are different consumers, not alternate runtime contracts (`FR-1163:14-24`). Token/timing and reasoning/cache-field precedents are reused, not reimplemented.

## Required revisions

### R-1: Freeze channel identity and dispatch attribution

Replace the underspecified exception contract in `FR-1163:84-100` with:

- Carry `collect_key: str`, a shallow list snapshot of `collected`, and `failures: list[MapFailure]`, alongside the existing map name and verdict. Keep the existing exception message. Preserve the existing two-argument construction with explicitly empty evidence; do not infer a configured key from the map name.
- The join supplies the actual configured collect/failures keys. Select failures by both `failure.map == map_name` and `failure.dispatch == verdict.dispatch`, then order by index. Do not attach historical failures or another map's records from shared channels.
- Define `collected` as the **whole existing collect-channel snapshot**, retaining reducer order and existing row shapes. It is not a current-dispatch-only list: append channels, shared channels and sequential reuse are already supported (`FR-1073:125-132,159-162,376`; `map_contract.py:183-190`), and collected rows lack dispatch identity (`map_compiler.py:201-214`).
- Print `<len(collected)> collected results in '<collect_key>' (<verdict.succeeded> succeeded in failing dispatch)`. With `--full`, display that explicitly labelled channel snapshot. Do not describe its length as the failing dispatch's success count. Preserve the full failure message in the exception and JSON; truncate only the text rendering at 200 message characters.

Add shared-channel and historical-dispatch failure records to a join witness. It must prove exact failure attribution, preserved collected evidence, and correct distinction between the channel length and current verdict count. Do not add dispatch identifiers to collected rows or redesign reducers under this FR.

### R-2: Bound execution failures and close the known exit holes

Replace the open-ended probes at `FR-1163:65-70` and "any exception after invoke starts" at lines 101-102 with a fixed boundary:

1. Partial-map text/JSON evidence is required for non-stream `invoke` and `ainvoke`. Exercise both with actual compiled graphs. Follow an exception cause only if a committed failing witness demonstrates wrapping; speculative cause-walking is not authorized.
2. Usage is emitted exactly once on execution exceptions, including the inner `TimeoutError` path, before exit 1. The existing timeout teardown remains guaranteed.
3. On the existing streaming error-event path, print tracked token/timing summaries once to stderr before its existing exit 1. Preserve already-streamed tokens. Explicitly defer streaming partial-map evidence and `--full` snapshot delivery; do not change `StreamEvent` or the executor's streaming protocol.
4. Pre-execution refusals and configuration failures keep their present behavior. Post-success output/export failures keep their present behavior and must not trigger duplicate usage or a second JSON object. Successful streaming output remains unchanged.
5. On failure, an enabled tracker emits a zero-call summary when no calls completed; disabled trackers emit nothing. On success, preserve the existing positive-call-only behavior and byte formatting (`graph_run_helpers.py:256-294`). A bare Python-node exception has no LLM callback usage; AC-05 currently demands a heading that the proposed reused helper would suppress (`FR-1163:124-125`).

Use one reporting policy at the CLI boundary, but do not route failed runs through `_emit_success_output` or any export helper.

### R-3: Specify the complete JSON failure object

Amend `FR-1163:103-106` to require one JSON stdout object for non-stream execution failure:

`{"status": "failed", "error": "<exception message>", "map": {...}, "token_usage": {...}, "timing": {...}}`

`map` is present only for completeness failure and contains `name`, `collect_key`, `verdict`, `collected`, and `failures`. Serialize verdict and failures as structured model objects and collected results using the existing state serializer conventions. `token_usage` and `timing` contain the corresponding existing tracker summaries only when their flags enabled those trackers, including zero-call summaries. Preserve all existing token-summary fields, including reasoning and cache read/write totals.

Do not print human-readable usage to JSON stdout. Any human-readable diagnostics remain on stderr. Successful JSON retains its existing shape. The current FR promises timing (`FR-1163:28-31,57-60`) but its failure object omits it, and presence-only AC-04 cannot detect stringified model records.

### R-4: Make acceptance discriminate the actual boundary behavior

Fold the revised criteria below into the FR. In particular:

- Exercise real compiled sync/async failures, both map variants, configured collect/failure keys, and shared/historical failure records.
- Compare known nonzero token values, including reasoning/cache totals, and known timing values; do not assert only headings or key presence.
- Separate zero-call failure from a run that first records usage and then raises a non-map error.
- Cover timeout and streaming error-event exits, both export mechanisms, disabled flags, JSON structure, and unchanged success output.
- State the exact targeted pytest command and strict traceability command. Existing output tests passing alone is not proof of byte identity; capture stable success cases with deterministic tracker summaries.

The listed live cached-map demo is not a required paid acceptance witness (`FR-1163:79`). No provider spend is authorized by this judgement.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 — evidence-bearing exception | `yamlgraph/models/map_results.py`: configured collect identity, snapshot and typed failures; unchanged completeness message/policy |
| D-2 — evidence capture | `yamlgraph/compile/map_contract.py`, `map_compiler.py`, `cached_map_compiler.py`: join arguments, snapshot and exact failure selection only |
| D-3 — failure presentation | `yamlgraph/cli/graph_commands.py`, `graph_run_helpers.py`: non-stream evidence/JSON, execution-failure usage, timeout and existing streaming error-event exits |
| D-4 — witnesses | `tests/unit/test_fr1163_map_failure_report.py` and directly affected existing map/cached-map/CLI tests |
| D-5 — traceability and record | FR-1163 implementation status and decisions; existing relevant requirement registry entries if needed; one fix changelog fragment; one diary reflection with **Seed:** |

Not authorized: changed `min_success`, tolerated-failure semantics, exit 0/1/3 policy, downstream execution after an unmet join, partial exports, durable persistence, checkpoint/reducer/result-row format changes, retry/resume, cache scheduling, executor or streaming event-model changes, successful-output redesign, new graph/prompt artifacts, enforcement-infrastructure edits, or paid live runs.

## Revised acceptance criteria

- [ ] AC-01: For each of `map` and `cached_map`, a real compiled three-item Python-worker graph with index 1 failing and absent `min_success` raises the existing completeness error. Its unchanged message/verdict, configured `collect_key`, two collected rows ordered 0 then 2, and single typed index-1 failure are asserted. Execute via both `invoke` and `ainvoke`.
- [ ] AC-02: A join state containing historical and other-map failures selects only records matching its map and verdict dispatch. Its collected snapshot preserves the entire channel without mutation; a fixture with channel length different from `verdict.succeeded` verifies the text labels both correctly.
- [ ] AC-03: Non-stream failure text contains the original error diagnostic, configured collect label and the index/type/message failure line. `--full` shows the snapshot; without it result values are absent. A long message remains intact in exception/JSON but is truncated in text.
- [ ] AC-04: A controlled-usage map failure with `--token-usage --timing` reports the expected token totals, call count, reasoning/cache totals and timing totals exactly once, and exits 1. Both flags disabled produce neither summary.
- [ ] AC-05: JSON failure stdout parses as exactly one object; verdict/failures are structured objects, collected content matches the exception, and enabled token/timing summaries equal the controlled tracker summaries. A non-map execution failure omits `map`; disabled tracker fields are absent. No decorative output appears on stdout.
- [ ] AC-06: A zero-call Python-node execution failure reports zero-call summaries for enabled flags and exits 1. A separate execution that records nonzero usage before a non-map exception retains those exact summaries.
- [ ] AC-07: An invocation raising `TimeoutError` exits 1 after one usage report and performs timeout cleanup. An existing streaming error event exits 1 after one stderr usage report, preserving token stdout and emitting no invented partial-map payload.
- [ ] AC-08: For an unmet join, a downstream sentinel never executes; neither configured `--export` outputs nor the `--export-state` destination is created. An explicitly unmet non-default threshold uses the same evidence/reporting path. Existing met-policy and completed-error exit-3 behavior remains unchanged.
- [ ] AC-09: Deterministic success snapshots remain byte-identical for text, `--full`, tracked/untracked usage, JSON and streaming. Configuration refusal and post-success export failure tests verify no newly added summaries or duplicate JSON objects.
- [ ] AC-10: A behavior-failing RED commit precedes GREEN. Run the combined FR-1163/FR-1073/FR-1161 targeted tests and affected CLI tests, the unit suite, existing applicable lint/format checks, and `python scripts/req_coverage.py --strict`; record commands and results in FR-1163. Every new test carries an appropriate requirement marker.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Commit R-1 through R-4 into FR-1163 before implementation; this draft alone grants no authority. | GATE |
| C-2 | Preserve FR-1073's unmet-join block and FR-1097's completed-run exit policy; failure presentation must never invoke exports. | GATE |
| C-3 | Keep channel snapshots and dispatch counts explicitly distinct; select failure records by both map and dispatch. | GATE |
| C-4 | Prove sync/async propagation and the known timeout/streaming exit paths with the named witnesses; do not silently discard evidence if a boundary differs. | GATE |
| C-5 | Do not change streaming transport, successful output, persistence or enforcement infrastructure. Adjacent work requires a separate FR. | GATE |
| C-6 | Complete RED/GREEN evidence, applicable checks, traceability and the FR implementation record before claiming completion. | GATE |
| C-7 | Any paid demonstration requires a separately recorded human spend decision; it is not needed for authority or deterministic acceptance. | GATE |

Authority granted: **conditional only** for the frozen exception-evidence and CLI failure-reporting correction after the required revisions are committed; no implementation authority is active on the reviewed FR as written.
