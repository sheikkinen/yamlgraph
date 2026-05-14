# Feature Request: FR-390 watcher validate-fix context normalization and sanity-check timeout budget

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-14

## Summary

Fix two post-enforce reliability defects in watcher2: stop forwarding unresolved placeholder vars into `validate_fix`, and increase `sanity_check` timeout budget from 600s to 1200s so successful enforce/validate runs are not followed by avoidable timeout failure.

## Value Statement

Watcher2 operators get deterministic post-enforce progression to submit/PR creation without manual recovery when validate diagnostics are initially absent or sanity review exceeds 10 minutes.

## Problem

Issue #390 reports two coupled failures in the post-enforce segment of watcher pipeline v2:

1. `validate_fix` is invoked with literal unresolved placeholders (`{precommit_output}`, `{validate_gate_output}`) when those keys are not yet present in context.
2. `sanity_check` has a 600s timeout budget that is too short for real runs involving FR review, diff review, diary write, and commit.

Observed impact in issue evidence: gh-382 and gh-383 completed enforce/validate phases but failed before submit/PR stage due post-enforce behavior.

## Research Findings

1. **Topic source missing locally; canonical issue used.**
   `.chaplain/processing/gh-390.md` is not present in this worktree snapshot, so GitHub issue #390 body was used as source of truth.

2. **First `validate_fix` pass runs before `validate_gate` can produce diagnostics.**
   Pipeline topology is `enforce_session -> validate_fix -> sanity_check -> validate_gate`; therefore `validate_gate_output` does not exist on first `validate_fix` invocation.

3. **Diagnostics are produced only after `validate_gate` executes.**
   `.chaplain/actions/validate_gate_action.py` sets `context["precommit_output"]` and `context["validate_gate_output"]` during validate gate execution.

4. **Unresolved placeholders are currently preserved as literal text.**
   `.chaplain/actions/yamlgraph_async_action.py` performs simple `{key}` string replacement; missing keys remain as literal `{placeholder}` and are passed through argv.

5. **Prompt-level guard exists but is downstream mitigation, not boundary normalization.**
   `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml` hides literal placeholder strings in rendered prompt, but unresolved placeholder payloads still cross action boundary.

6. **Timeout budget mismatch is real across post-enforce boundaries.**
   `enforce_session` has 3600s, while both pipeline `sanity_check` action timeout and sanity-check graph node timeout are 600s.

## Objectives

1. Ensure `validate_fix` receives either real diagnostics or explicit empty values, never unresolved placeholder literals.
2. Raise `sanity_check` timeout budget to at least 1200s across the full sanity-check execution boundary.
3. Preserve existing post-enforce routing semantics (`PASS`/`WARN` to `validate_gate`, retry behavior unchanged).

## Constraints

1. Keep scope limited to post-enforce watcher orchestration and directly-coupled action/graph boundaries.
2. Do not change watcher FSM topology, event names, or validate-gate retry policy.
3. Do not alter prompt intent/ownership boundaries (enforce vs validate vs sanity responsibilities).
4. No new dependencies.

## Proposed Solution

### In scope

1. Normalize unresolved placeholder vars at yamlgraph async action boundary for validate-style var payloads:
   - if a configured var value remains an unresolved full placeholder token after context substitution, pass an explicit empty string value instead of literal `{placeholder}`.
   - preserve current behavior when concrete context values exist (including retry passes with real diagnostics).
2. Increase sanity-check timeout budget from 600s to 1200s in:
   - `.chaplain/config/watcher-pipeline-v2.yaml` (`actions.sanity_check[0].timeout`)
   - `.chaplain/graphs/watcher-enforce/sanity-check-session.yaml` (`nodes.sanity_check.timeout`)
3. Add focused acceptance tests that lock these contracts.

### Out of scope

1. Refactoring watcher dispatcher behavior or PR submission flow.
2. Redesigning validate prompt content or output schema.
3. Broad timeout tuning for plan/judge/validate nodes not implicated by this issue.

## Acceptance Criteria

- [x] **AC-01:** First-pass `validate_fix` execution does not pass literal unresolved placeholders (e.g., `{precommit_output}` / `{validate_gate_output}`) in yamlgraph `--var` payloads.
- [x] **AC-02:** When `precommit_output`/`validate_gate_output` exist in context (retry pass), `validate_fix` forwards their real values unchanged.
- [x] **AC-03:** Pipeline `sanity_check` action timeout is `>= 1200` seconds.
- [x] **AC-04:** Sanity-check session graph node timeout is `>= 1200` seconds.
- [x] **AC-05:** `sanity_check` routing remains unchanged: `PASS` and `WARN` both proceed to `validate_gate`.
- [x] **AC-06:** Focused RED acceptance tests are added for AC-01..AC-05.

## Failing Acceptance Tests (RED plan)

Create:

- `tests/unit/test_fr390_watcher_validate_fix_context_and_sanity_timeout.py`

Planned RED tests:

1. `test_ac01_first_validate_fix_pass_omits_literal_placeholder_payloads`
2. `test_ac02_retry_validate_fix_pass_forwards_real_gate_diagnostics`
3. `test_ac03_pipeline_sanity_check_timeout_is_at_least_1200`
4. `test_ac04_sanity_graph_node_timeout_is_at_least_1200`
5. `test_ac05_sanity_pass_warn_routing_to_validate_gate_preserved`

RED command:

```bash
pytest tests/unit/test_fr390_watcher_validate_fix_context_and_sanity_timeout.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
rg -n 'precommit_output: "\{precommit_output\}"|validate_gate_output: "\{validate_gate_output\}"' .chaplain/config/watcher-pipeline-v2.yaml
rg -n 'sanity_check:|timeout:\s*600' .chaplain/config/watcher-pipeline-v2.yaml .chaplain/graphs/watcher-enforce/sanity-check-session.yaml
```

## Alternatives Considered

1. **Keep placeholder literals and rely only on prompt-level filtering**
   Rejected: symptom mitigation remains downstream; boundary still forwards invalid placeholder payloads.

2. **Remove diagnostics vars from `validate_fix` entirely**
   Rejected: would regress the validate-gate diagnostics handoff contract (FR-321 intent).

3. **Increase only pipeline timeout but not graph-node timeout**
   Rejected: partial remediation; inner graph timeout can still terminate at 600s.

## Judgement

**Verdict:** APPROVE — 2026-05-14

Both problems confirmed by code reading:
- `yamlgraph_async_action.py` lines 44–48 preserves unresolved `{placeholder}` literals on missing context keys.
- `sanity_check` action timeout (line 304 pipeline YAML) and graph node timeout (line 33 sanity-check-session.yaml) are both 600s.

Implementation guidance:
- Use the `_is_placeholder()` pattern already in `validate_gate_action.py` (lines 40–42) for the boundary normalization in `yamlgraph_async_action.py`.
- Tests should use `@pytest.mark.req("REQ-YG-318")`.
- Scope is frozen. No FSM topology changes. No new dependencies.

## Related

- Issue #390: <https://github.com/sheikkinen/yamlgraph/issues/390>
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/actions/yamlgraph_async_action.py`
- `.chaplain/actions/validate_gate_action.py`
- `.chaplain/graphs/watcher-enforce/sanity-check-session.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`
- `tests/unit/test_fr321_watcher_validate_fix_gate_diagnostics_handoff.py`
- Topic source requested: `.chaplain/processing/gh-390.md` (not present in this worktree snapshot)

## Implementation Notes

1. Added boundary normalization in `.chaplain/actions/yamlgraph_async_action.py` for unresolved full-placeholder values of `precommit_output` and `validate_gate_output`; unresolved placeholders are now forwarded as empty strings.
2. Increased sanity timeout budget to 1200s in both `.chaplain/config/watcher-pipeline-v2.yaml` (`actions.sanity_check[0].timeout`) and `.chaplain/graphs/watcher-enforce/sanity-check-session.yaml` (`nodes.sanity_check.timeout`).
3. Added `tests/unit/test_fr390_watcher_validate_fix_context_and_sanity_timeout.py` with AC-01..AC-05 coverage tagged to `REQ-YG-318`.
