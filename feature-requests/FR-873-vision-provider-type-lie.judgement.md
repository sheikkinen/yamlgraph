# Judgement: FR-873 Vision Boundary - Provider Type Lie Kills the Run (DRAFT)

**Verdict:** APPROVED WITH REVISIONS - the defect is real and the repair belongs at the vision/gate boundary, but authority activates only after the FR corrects the witness, freezes the raw-output capture mechanism, types the invalid-description path, and tightens the acceptance criteria.

**Reviewed against:** `feature-requests/FR-873-vision-provider-type-lie.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.judgement.md`; `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md`; `capabilities/CAP-117-race-node-parse-json-content-normalization.yaml`; `docs/diary/diary-2026-08-24-twenty-gates-and-a-human-found-the-fire.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `ARCHITECTURE.md`; GitHub Actions run `sheikkinen/deviant-daily#32688775537`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:tools/vision.py`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:tools/gate.py`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:tools/steps.py`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:graph.yaml`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:tests/test_gate.py`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:tests/test_steps.py`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:tests/test_vision_size.py`; `sheikkinen/deviant-daily@12bd530cbaeb6f8149e39c0f72f0d222600b4387:tests/test_external_constraints.py`.

**Prior art:** dispositioned below — FR-826 (the describe→gate contract preserved, R-5 gate-as-sole-decider), FR-863 (same defect class one boundary over: an external constraint not mirrored inward), CAP-117 (the existing race-node JSON-normalization cure and the precedent to follow). FR-862 and FR-872 marked non-overlap (dispatch surface, ramp tooling). No REJECTED prior art occupies this territory. FR-873 is the subject FR.

## What is sound

The production witness is real: run `32688775537` failed in the pipeline step with `tool_call node 'describe': tool 'describe_step' failed: 1 validation error for PostDescription`, and Pydantic rejected `paragraphs` because the provider returned a JSON-encoded string where `PostDescription.paragraphs` requires `list[str]` (GitHub Actions run `32688775537`: lines 417-430). That matches the FR's core diagnosis that structured output is a request, not a provider guarantee (`feature-requests/FR-873-vision-provider-type-lie.md:25-29`, `48-51`).

The target code confirms both defects. `describe_image()` currently binds `with_structured_output(PostDescription)` and immediately calls `structured.invoke([message])`, so validation occurs inside the describe node before any gate can classify the shape failure (`sheikkinen/deviant-daily@12bd530c...:tools/vision.py:91-108`). The graph marks `describe` as `on_error: fail`, then routes to `gate` only after a successful describe result (`sheikkinen/deviant-daily@12bd530c...:graph.yaml:60-79`, `104-113`). `gate_step()` already commits a `skipped` ledger row for `evaluate_gate(...).publish == False`, so routing schema-shaped failures into that path preserves the FR-826 gate contract rather than inventing a second decider (`sheikkinen/deviant-daily@12bd530c...:tools/steps.py:107-134`; `feature-requests/FR-826-deviantart-daily-repo.md:190-200`).

The prior-art chain is valid. FR-863 names the same external-boundary class: constraints known at the provider/API boundary were not mirrored into local models (`feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md:28-34`, `114-122`). CAP-117 records the yamlgraph core precedent for normalizing provider content before parsing JSON (`capabilities/CAP-117-race-node-parse-json-content-normalization.yaml:1-9`; `ARCHITECTURE.md:690-716`). Repo doctrine says normalize at schema/provider boundaries and treat provider type lies as boundary facts, not downstream surprises (`.github/copilot-instructions.md:50-58`, `98-117`).

Scope is one concern: schema-shaped describe output currently bypasses the publish gate. Repairing narrow list-field JSON strings and converting unrecoverable schema failures into a typed skip are coupled halves of that same concern, not a split. Strategic classification: **Contrib/product repo bug fix** for `sheikkinen/deviant-daily`, not a YAMLGraph framework primitive.

## Required revisions

### R-1: Correct the witness and first-event language

Revise the FR so its incident description matches the cited run. The run metadata says `32688775537` was `workflow_dispatch` / `publish-now`, not the scheduled daily cron, and its log shows it drew `2026-08-24#1`, while the ledger at the run-start SHA already contained a published `2026-08-24#0` row. Current `main` contains the failed run's `2026-08-24#1` `drawn` row, not a `skipped` row.

Fold this by changing the first consumer/event and problem text from "daily publish ... published nothing" to the precise claim: a manual same-day publish attempt for slot `2026-08-24#1` failed red after the draw transition; the shape failure produced no `skipped` classification for that slot. Keep the recurrence argument, but do not claim the cited run proves that the whole day had no publication.

### R-2: Freeze how raw provider output is captured before final validation

Revise S-1 because the current proposed location is not mechanically possible as written. `with_structured_output(PostDescription)` validates inside `structured.invoke()` before `describe_image()` receives `result`, so code "before validation" cannot repair `paragraphs` unless the invocation surface changes (`sheikkinen/deviant-daily@12bd530c...:tools/vision.py:105-108`).

Fold this by specifying the exact two-stage contract: capture a raw structured payload whose list-typed fields are not final-validated, run the narrow repair on `paragraphs`, `tags`, and `mature_classification`, then pass the repaired payload through `PostDescription.model_validate(...)` exactly once. Acceptable shapes include a local `RawPostDescription` Pydantic model with those three fields typed broadly enough to observe provider lies, or LangChain raw structured output if it exposes the tool-call arguments directly. The final exported type remains `PostDescription`; no downstream consumer may receive `str | list[str]`.

### R-3: Type the schema-failure marker and route it through `evaluate_gate`

Revise S-2 so the skip path is not an ad-hoc dict that `PostDescription` will ignore or misdiagnose. Today `evaluate_gate()` catches `ValidationError` from `PostDescription.model_validate(raw)` and returns `schema: ...`; an added `{"__invalid__": True, "reason": ...}` marker would otherwise be just extra input to a model that defaults to ignoring unknown keys, likely producing a generic missing-field error instead of the field-specific reason (`sheikkinen/deviant-daily@12bd530c...:tools/gate.py:88-98`).

Fold this by defining a typed invalid-description boundary, for example a small Pydantic/dataclass value with `{valid: false, reason: str, field: str}` or an explicit `__invalid__` branch consumed before `PostDescription.model_validate(...)` inside `evaluate_gate()`. `describe_step()` may create that value only for schema-shaped failures from final validation or from the narrow repair function. `gate_step()` must remain the component that commits the skip; `describe_step()` must not decide publish/skip or write the ledger.

### R-4: Separate repair failure from genuine execution failure without broad catches

Revise the exception contract. The FR says `json.loads` may raise and "caller records skip" (`feature-requests/FR-873-vision-provider-type-lie.md:91-99`), but S-2 says only `ValidationError` is caught (`feature-requests/FR-873-vision-provider-type-lie.md:108-115`). That leaves invalid JSON strings either escaping red or requiring a broad catch, both violating the stated non-goal that only schema-shaped failures become skips (`feature-requests/FR-873-vision-provider-type-lie.md:123-125`) and repo doctrine against silent/broad fallbacks (`.github/copilot-instructions.md:217-221`).

Fold this by introducing a narrow local exception or result type for "schema-shaped unrecoverable description" that includes the offending field and reason. The repair helper must convert `json.JSONDecodeError`, non-list JSON, and non-`str` list members into that schema-failure value; missing API keys, network/API errors, image decoding errors, roster errors, and ledger commit errors must continue to raise and make the run red.

### R-5: Tighten stale or ambiguous acceptance criteria

Revise the AC list so every item is mechanically checkable against the current target repo. AC-07's "byte-identical" wording is ambiguous because `PostDescription` already transforms valid inputs such as title trimming and tag normalization (`sheikkinen/deviant-daily@12bd530c...:tools/gate.py:44-62`; `tests/test_external_constraints.py:28-47`). AC-08 says "exactly one skipped ledger row" but the failed path already has a prior `drawn` row for the slot, so the criterion must specify exactly one additional `skipped` transition for the same `(date, slot)`. AC-09 combines multiple branches across describe, publish, and image handling; keep it, but split it by failure class. AC-11's "128 existing tests" is stale against the cited target, whose FR-863 and tests cite 145 tests (`feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md:221-231`).

Fold the revised AC list below into the FR verbatim or with equivalent precision.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-873-vision-provider-type-lie.md` folding R-1 through R-5 |
| D-2 | `sheikkinen/deviant-daily:tools/vision.py` raw-output capture, narrow list-field repair, final `PostDescription` validation, and repair logging |
| D-3 | `sheikkinen/deviant-daily:tools/gate.py` typed invalid-description handling inside the existing gate evaluation path |
| D-4 | `sheikkinen/deviant-daily:tools/steps.py` describe wrapper that converts only schema-shaped description failures into the typed invalid-description value |
| D-5 | Target-repo tests covering repair success, unrecoverable schema skip, non-schema red failures, logging, and ledger transition behavior |
| D-6 | FR implementation-status update with run IDs, test command/result, and any deviations from frozen scope |

Not authorized: YAMLGraph core/runtime changes; graph or prompt artifact changes unless separately routed through the graph-authoring contract; retrying the LLM as the primary fix; loosening downstream `PostDescription`/publisher types to accept `str | list[str]`; changing DeviantArt publish policy, confidence semantics, mature policy, roster behavior, corpus draw semantics, ledger idempotency, workflow triggers, or secret handling; converting missing secrets, network/API failures, image decoding failures, roster failures, ledger commit failures, or publish failures into green skips.

## Revised acceptance criteria

- [ ] AC-01: The FR is revised to state the exact witness: run `32688775537` was `workflow_dispatch` / `publish-now`, failed on `2026-08-24#1` after draw, and left no `skipped` row for that slot.
- [ ] AC-02: A condemning test reproduces the cited provider type lie: a raw describe payload with `paragraphs` as a JSON-encoded string fails before the fix and, after the fix, produces a valid `PostDescription` whose `paragraphs` is `list[str]` with the same element text.
- [ ] AC-03: The same narrow repair is covered for `tags` and `mature_classification`; repaired `mature_classification` still passes through the existing allowed-enum validation.
- [ ] AC-04: The repair helper attempts `json.loads` only for string values in the three authorized list fields, repairs only JSON arrays where every element is `str`, and leaves non-string already-valid list values to final validation unchanged.
- [ ] AC-05: Invalid JSON strings in each authorized field do not escape the describe node; they produce the typed invalid-description value with a `schema:` reason naming the field.
- [ ] AC-06: Valid JSON that is not `list[str]` is not repaired; object JSON, list-of-int JSON, and nested-list JSON each produce the same typed invalid-description path with field-specific reasons.
- [ ] AC-07: A well-formed provider response follows the same final `PostDescription` validation semantics as before; no repair log is emitted and no new mutation occurs beyond existing validators such as title trimming and tag normalization.
- [ ] AC-08: Every successful repair emits exactly one structured log line naming the repaired field; tests assert the field names and assert no log for the no-repair path.
- [ ] AC-09: `evaluate_gate()` recognizes the typed invalid-description value and returns `publish=False` with the supplied `schema:` reason without attempting normal `PostDescription` validation first.
- [ ] AC-10: `gate_step()` commits exactly one additional `skipped` ledger row for the same `(date, slot)` when it receives an invalid-description result; the row reason starts with `schema:` and names the offending field.
- [ ] AC-11: A graph/tool-level test proves a schema-shaped describe failure exits green after the skipped row is committed, following the existing `gate -> END` non-publish edge.
- [ ] AC-12: Missing API key, provider/network error, undecodable image bytes, roster failure, ledger commit failure, and publish failure each remain red; no broad exception handler converts them to skips.
- [ ] AC-13: A source-level test asserts `describe_step` contains no publish/skip decision and no ledger write; only `gate_step` records skipped rows.
- [ ] AC-14: Target-repo tests and formatter/linter commands that already exist for `sheikkinen/deviant-daily` pass; the FR records the actual test count observed, not a stale hard-coded count.
- [ ] AC-15: A live post-fix `workflow_dispatch` run completes green; the FR records the run ID and the resulting ledger transition (`published` or `skipped`). If the live run does not exercise a repair, the unit/graph tests remain the repair proof.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-873-vision-provider-type-lie.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | The final `PostDescription` contract remains strict; do not export `str | list[str]` list fields to downstream publish/render code. | GATE |
| C-4 | Only schema-shaped describe-output failures may become green skips; operational failures and side-effect failures must stay red. | GATE |
| C-5 | The gate remains the sole publish/skip ledger writer; `describe_step` may return a typed invalid-description value but must not write state or decide publication. | GATE |
| C-6 | If enforcement requires editing `graph.yaml` or any `prompts/*.yaml`, stop and route that artifact change through the graph-authoring contract. | GATE |
| C-7 | If the chosen raw-output capture mechanism cannot expose provider tool-call arguments before final Pydantic validation, stop and revise the FR rather than adding a broad catch or a downstream loose type. | GATE |

Authority granted: after the required revisions are folded, enforcement may implement the narrow deviant-daily vision/gate boundary repair and its tests within the frozen scope above.
