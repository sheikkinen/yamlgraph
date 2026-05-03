# Feature Request: FR-310 watcher2 validate + precommit states

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented
**Effort:** 0.5–1 day
**Requested:** 2026-05-03
**Judged:** 2026-05-03
**Amended:** 2026-05-03

## Summary

Add explicit `validate` and `precommit_check` states to the watcher2 v2 pipeline so enforcement and quality-gating are separated by contract.

## Value Statement

Watcher2 operators get a judgeable, fail-closed quality boundary where pre-commit outcomes are mechanically enforced outside the enforce session.

## Problem

The current v2 FSM still routes `enforce_session -> done`, so quality checks remain bundled inside the same enforce copilot session:

1. `.chaplain/config/watcher-pipeline-v2.yaml` has no `validate` or `precommit_check` state.
2. `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml` instructs the enforce node to run both pytest and pre-commit itself.
3. FR-305 explicitly targeted an enforce⇄validate loop, but its own acceptance criteria still show validate-loop criteria unchecked.

This keeps the gate porous: the same agent that implements can also self-report validation completion.

## Objectives

1. Insert a distinct post-enforce validation phase before `done`.
2. Add a mechanical pre-commit gate that cannot be bypassed by LLM output shaping.
3. Feed pre-commit failure output back into a fresh validate session for remediation.
4. Cap remediation churn with explicit loop-attempt limits.

## Constraints

- Scope is limited to watcher2 FSM v2 artifacts under `.chaplain/` (config + enforce/validate graph prompts + tests).
- No refactor of legacy `.chaplain/watcher2.sh` in this FR.
- Preserve existing `setup -> plan -> commit_plan -> judge -> enforce_session` semantics.
- Keep `done` behavior unchanged (push/PR/CI/merge/cleanup).

## Research Findings

- **Current FSM gap:** `watcher-pipeline-v2.yaml` transitions directly from `enforce_session` to `done` on `pass`, with no validation intermediary.
- **Prompt boundary mismatch:** `enforce-session.yaml` prompt currently embeds:
  - `pytest tests/ --no-cov -x`
  - `pre-commit run --all-files`
  This couples implementation and validation in one session.
- **Reusable prior art exists:** `.chaplain/actions/precommit_action.py` already codifies retry semantics (`max_attempts` + attempt counter), proving loop control is an established pattern even though it is not wired in v2 config.
- **Existing tests currently pass without the new states:** `tests/unit/test_fr305_watcher_pipeline_v2.py` (54 passing) confirms the missing states are not presently enforced.

## Proposed Solution

Introduce two states between `enforce_session` and `done`:

```text
enforce_session -> validate -> precommit_check -> done
                       ^             |
                       |             |
                       +-- fix_needed+
                     (max 5 attempts -> failed)
```

### 1. FSM changes (`.chaplain/config/watcher-pipeline-v2.yaml`)

- Add new states: `validate`, `precommit_check`.
- Replace transition:
  - `enforce_session --pass--> done`
  with:
  - `enforce_session --enforce_done--> validate`
  - `validate --validate_done--> precommit_check`
  - `precommit_check --pass--> done`
  - `precommit_check --fix_needed--> validate`
  - `precommit_check --error--> failed` (attempt cap reached)

### 2. Validate state (fresh copilot session)

- Add `.chaplain/graphs/watcher-enforce/validate-session.yaml` and prompt `prompts/validate-session.yaml`.
- Validate node responsibilities:
  1. Read FR + latest pre-commit output context.
  2. Run `ruff check --fix` and `ruff format`.
  3. Run `pytest tests/unit/ -q --no-cov -x`.
  4. Apply fixes and commit remediation.
- Must run as a fresh session (no resume from `enforce_session`).

### 3. Pre-commit gate state (reuse `precommit` action)

- `precommit_check` uses the existing `precommit` action type (`.chaplain/actions/precommit_action.py`).
- Config:
  ```yaml
  precommit_check:
    - type: precommit
      max_attempts: 5
      success: pass
      retry: fix_needed
      cwd: "{wt_dir}"
      description: "🔒 Pre-commit gate (mechanical)"
  ```
- The `precommit` action already implements:
  - Attempt counter (`context["precommit_attempt"]`, defaults to 0)
  - Max-attempt cap → emits `error` on exhaustion
  - Configurable `success` and `retry` events
  - Auto-staging of fixed files
- **Enhancement required:** Extend `precommit_action.py` to store `context["precommit_output"] = result.stdout` on failure, so the validate prompt receives structured failure context via `{precommit_output}` template substitution.

### 4. Enforce prompt boundary update

- Update `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml` so enforce focuses on implementation and commit preparation.
- Remove enforce responsibility for authoritative pre-commit and pytest gate completion (those belong to `validate` + `precommit_check` states).

## Acceptance Criteria

- [x] **AC-01:** `watcher-pipeline-v2.yaml` defines `validate` and `precommit_check` states.
- [x] **AC-02:** `watcher-pipeline-v2.yaml` no longer has direct `enforce_session -> done` transition.
- [x] **AC-03:** Transition path includes `enforce_session -> validate -> precommit_check -> done`.
- [x] **AC-04:** `precommit_check` loops `fix_needed -> validate` and routes to `failed` after max attempts.
- [x] **AC-05:** `precommit_check` uses `type: precommit` action with `max_attempts`, `success`, and `retry` config keys.
- [x] **AC-06:** `precommit_action.py` stores failure output in `context["precommit_output"]` for validate-step remediation.
- [x] **AC-07:** New validate graph and prompt files exist at `.chaplain/graphs/watcher-enforce/validate-session.yaml` and `.../prompts/validate-session.yaml`.
- [x] **AC-08:** Validate prompt includes `ruff check --fix`, `ruff format`, and `pytest tests/unit/ -q --no-cov -x`.
- [x] **AC-09:** Enforce-session prompt no longer claims ownership of pre-commit gate execution.
- [x] **AC-10:** Acceptance tests are added in `tests/unit/test_fr310_watcher2_validate_precommit_states.py` and fail on current implementation until the new states and contracts are implemented.

## Alternatives Considered

1. **Keep current single `enforce_session` validation flow** — rejected; preserves self-validation coupling.
2. **Use only `precommit_action.py` without a separate validate state** — rejected; doesn’t provide a fresh remediation session with structured failure context.
3. **Move both pytest and pre-commit to one bash state** — rejected for this FR; removes guided remediation loop requested for validate.

## Related

- Topic: `.chaplain/processing/validate-precommit-states.md`
- Parent: `feature-requests/FR-305-watcher-pipeline-fsm-simplification.md`
- FSM: `.chaplain/config/watcher-pipeline-v2.yaml`
- Enforce graph: `.chaplain/graphs/watcher-enforce/enforce-session.yaml`
- Enforce prompt: `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml`
- Existing tests: `tests/unit/test_fr305_watcher_pipeline_v2.py`

---

## Judgement — AMEND

**Verdict:** The problem is real and the two-phase architecture (LLM remediation + mechanical gate) is the right direction. However, the proposed `precommit_check` mechanism is underspecified and contradicts the capabilities of the chosen action type. Amendments required before enforcement.

### What's sound

1. **Problem is real.** Self-validation coupling (same agent implements and certifies) is the anti-pattern the Scripture traps call out. Separating enforce from validation is correct.
2. **Two-phase design is correct.** LLM remediation (`validate`) + mechanical gate (`precommit_check`) is the right split. The LLM fixes; the gate judges. No agent marks its own homework.
3. **Scope is well-bounded.** Preserving existing setup→plan→commit_plan→judge→enforce_session flow and limiting changes to post-enforce states is minimal.
4. **Loop cap prevents churn.** Max 5 attempts before failing is a reasonable limit.

### What must be amended

#### 1. Three-way event routing is impossible with `bash_context`

The FR proposes `precommit_check` as `type: bash_context` but requires **three** outcomes:
- `pass` → done (pre-commit clean)
- `fix_needed` → validate (pre-commit failed, attempts remain)
- `error` → failed (attempts exhausted)

`bash_context` can only emit **two** events: `success` (exit 0) or `error` (non-zero). There is no conditional routing based on attempt count.

**Fix:** Use the existing `precommit` action type (`.chaplain/actions/precommit_action.py`) which already implements:
- Attempt counter (`context["precommit_attempt"]`)
- Max-attempt cap with `error` on exhaustion
- Configurable `success` and `retry` events
- Auto-staging of fixed files

This is proven infrastructure. The FR's Research Findings even cite it: *"`.chaplain/actions/precommit_action.py` already codifies retry semantics"* — then ignores it. Use it.

Config would be:
```yaml
precommit_check:
  - type: precommit
    max_attempts: 5
    success: pass
    retry: fix_needed
    cwd: "{wt_dir}"
    description: "🔒 Pre-commit gate (mechanical)"
```

#### 2. AC-05 and AC-06 need revision

- **AC-05** is fine as-is (transition `precommit_check -> failed on error`) — the `precommit` action already emits `error` on attempt exhaustion.
- **AC-06** must change:
  - Assert `type == "precommit"` (not `bash_context`)
  - Drop `capture_keys` assertions (precommit action uses `context["precommit_attempt"]` directly, not JSON capture)
  - Assert `max_attempts` config exists
  - Assert `retry` event config exists
  - Optionally: assert `precommit_output` capture if we want to pass failure output to validate. This requires extending the `precommit` action to write output to context — a small, justified enhancement.

#### 3. `precommit_output` feedback to validate — specify the mechanism

The FR says precommit failure output should feed into the validate session for remediation (AC-06) but doesn't specify how. Two options:

**Option A (minimal):** The `precommit` action already logs failure output. The validate copilot session can read the log or re-run pre-commit itself to see what failed. No code change needed.

**Option B (explicit):** Extend `precommit_action.py` to store `context["precommit_output"] = result.stdout` on failure. The validate prompt then uses `{precommit_output}` template substitution. Small, clean enhancement.

Recommend **Option B** — it's 2 lines of code in the existing action and gives the validate prompt structured failure context.

#### 4. `validate_attempt` counter initialization

The FR doesn't specify where `validate_attempt` (or `precommit_attempt`) is initialized. The existing `precommit` action uses `context.get("precommit_attempt", 0)` — defaulting to 0 on first run. This is fine but should be documented in the FR.

#### 5. Type is "Feature" not "Bug"

Adding two new FSM states is a feature, not a bug. Fixed in header.

### Amended acceptance criteria

Replace AC-05 and AC-06 with:

- [ ] **AC-05:** `precommit_check` transitions to `failed` on `error` (attempt cap exhausted).
- [ ] **AC-06:** `precommit_check` uses `type: precommit` action (not `bash_context`) with `max_attempts`, `success`, and `retry` config keys. The `precommit` action stores failure output in `context["precommit_output"]` for validate-step remediation.

### Amended test for AC-06

```python
def test_ac06_precommit_check_uses_precommit_action_with_retry(self):
    config = _load_yaml(PIPELINE_V2)
    action = _action_for(config, "precommit_check")
    assert action["type"] == "precommit", "precommit_check must use precommit action type"
    assert action.get("max_attempts", 0) > 0, "must configure max_attempts"
    assert "retry" in action, "must configure retry event for fix_needed routing"
    assert "success" in action, "must configure success event"
```

### Required changes to existing code

1. **`precommit_action.py`**: Add `context["precommit_output"] = result.stdout` on failure (2 lines).
2. **Tests**: Update AC-06 test to assert `type: precommit` instead of `type: bash_context`.
3. **FR**: Update proposed solution section 3 to reference `precommit` action type.

### Decision: freeze scope after amendments

Once AC-05/AC-06 and the proposed solution section are amended as above, scope is frozen. Enforce may proceed.
