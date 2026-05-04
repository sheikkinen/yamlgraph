# Feature Request: FR-321 watcher validate_fix gate diagnostics handoff

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-04

## Summary

Pass deterministic `validate_gate_output` diagnostics into `validate_fix` so remediation sees the actual gate failures (especially diary-parity), and treat first-pass `precommit_output` as empty context instead of rendering unresolved placeholder text.

## Value Statement

Watcher2 maintainers get actionable remediation loops (instead of blind retries), reducing repeated validate cycles where the LLM cannot see the failing gate reason.

## Problem

GitHub issue #318 identifies a broken feedback loop between `validate_gate` and `validate_fix`:

1. `validate_gate` stores structured diagnostics in `context["validate_gate_output"]`, but `validate_fix` does not receive that value.
2. `validate_fix` currently depends on `precommit_output`, which does not fully represent gate failures like `diary_parity`.
3. On first `validate_fix` pass, `precommit_output` can render as literal `{precommit_output}`, producing misleading prompt context.

Impact:

- `validate_fix` retries can loop without seeing the real deterministic gate failure.
- Diary-parity failures are invisible to the remediation prompt even when `validate_gate` has already diagnosed them.

## Research: Existing Patterns and Prior Art

1. **Diagnostics already exist at the boundary.**
   `.chaplain/actions/validate_gate_action.py` writes both `context["precommit_output"]` and `context["validate_gate_output"]` with structured `checks` and `failures`.

2. **Pipeline handoff is incomplete.**
   `.chaplain/config/watcher-pipeline-v2.yaml` `validate_fix` action passes `precommit_output` but not `validate_gate_output`.

3. **Validate graph/prompt are precommit-only today.**
   `.chaplain/graphs/watcher-enforce/validate-session.yaml` state/variables include `precommit_output` only; `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml` renders only that channel.

4. **Architecture intent already covers deterministic gate + remediation split.**
   `REQ-YG-318` / `CAP-140` define `validate_fix` + `validate_gate` cooperation, but current implementation misses diagnostics plumbing needed for effective retries.

5. **Related prior fix is adjacent, not sufficient.**
   FR-319 hardens shell-safe var transport, but does not add `validate_gate_output` to the remediation prompt contract.

## Objectives

1. Ensure `validate_fix` receives `validate_gate_output` from pipeline context on retry passes.
2. Expose gate diagnostics in validate prompt content so remediation can target actual failing checks.
3. Preserve existing FSM topology and retry semantics while removing misleading first-pass placeholder output.

## Constraints

1. Scope is limited to validate diagnostics handoff (pipeline vars, validate graph state/vars, validate prompt contract, and directly coupled tests).
2. No changes to watcher FSM state topology or event routing.
3. No relaxation of deterministic gate checks; fix feedback visibility, not enforcement strictness.
4. Apply fix at watcher validate callsite/prompt boundary; avoid unrelated broad behavior changes.

## Proposed Solution

### In scope

1. Update `.chaplain/config/watcher-pipeline-v2.yaml` `validate_fix` vars to include:
   - `validate_gate_output: "{validate_gate_output}"`
2. Update `.chaplain/graphs/watcher-enforce/validate-session.yaml`:
   - Add `validate_gate_output` in `state`
   - Pass it to node variables for prompt rendering
3. Update `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`:
   - Add a dedicated diagnostics section rendering `validate_gate_output` when present
   - Treat unresolved/literal `{precommit_output}` as first-pass/no-diagnostics context
4. Add focused unit tests that lock this handoff contract.

### Out of scope

1. Redesigning `validate_gate` rules or retry counts.
2. Modifying unrelated `yamlgraph_async_action` global substitution semantics.
3. Any changes to enforce, sanity-check, done, or dispatcher behavior beyond diagnostics handoff.

## Acceptance Criteria

- [x] **AC-01:** `watcher-pipeline-v2.yaml` `validate_fix` action passes `validate_gate_output` variable from FSM context.
- [x] **AC-02:** `watcher-enforce/validate-session.yaml` declares and forwards `validate_gate_output` state for prompt consumption.
- [x] **AC-03:** `watcher-enforce/prompts/validate-session.yaml` explicitly renders validate-gate diagnostics (checks/failures context) when provided.
- [x] **AC-04:** First `validate_fix` pass treats unresolved/literal `{precommit_output}` as no prior diagnostics (no misleading literal output block).
- [x] **AC-05:** Existing validate retry topology remains unchanged (`validate_gate` retry event still routes to `validate_fix`; pass/error routing unchanged).
- [x] **AC-06:** Unit tests are added for AC-01..AC-05.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr321_watcher_validate_fix_gate_diagnostics_handoff.py`

Test cases:

1. `test_ac01_validate_fix_action_passes_validate_gate_output_var`
2. `test_ac02_validate_session_graph_declares_validate_gate_output_state_and_variable`
3. `test_ac03_validate_prompt_renders_validate_gate_diagnostics_section`
4. `test_ac04_validate_prompt_handles_literal_precommit_placeholder_as_first_pass`
5. `test_ac05_validate_gate_retry_topology_unchanged`

RED command:

```bash
pytest tests/unit/test_fr321_watcher_validate_fix_gate_diagnostics_handoff.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
rg -n 'validate_gate_output:\s*"\{validate_gate_output\}"' .chaplain/config/watcher-pipeline-v2.yaml
rg -n 'validate_gate_output' .chaplain/graphs/watcher-enforce/validate-session.yaml .chaplain/graphs/watcher-enforce/prompts/validate-session.yaml
```

## Alternatives Considered

1. **Use only `precommit_output` and keep current prompt shape**
   Rejected: cannot surface deterministic gate failures (e.g., `diary_parity`) that are not encoded in pre-commit output.

2. **Move remediation logic into deterministic gate action**
   Rejected: violates separation of concerns (`validate_gate` should diagnose/enforce; `validate_fix` should remediate).

3. **Change global placeholder substitution behavior in shared async action**
   Rejected for this FR: broader blast radius than needed; this issue is solvable at watcher validate handoff boundary.

## Related

- GitHub issue #318: <https://github.com/sheikkinen/yamlgraph/issues/318>
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/actions/validate_gate_action.py`
- `.chaplain/graphs/watcher-enforce/validate-session.yaml`
- `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`
- `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py`
- `feature-requests/FR-319-watcher-yamlgraph-async-shell-safe-vars.md`
- Topic source requested: `.chaplain/processing/gh-318.md` (not present in this worktree)
- Canonical topic source used for drafting: GitHub issue #318
