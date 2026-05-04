# Feature Request: FR-325 Demo-gate validates demo-output.log content

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-04

## Summary

Strengthen demo-proof enforcement so `demo-gate` rejects failed or empty `demo-output.log` artifacts instead of only checking file presence.

## Value Statement

Maintainers get enforcement that demo logs represent successful demo runs, preventing broken executions from passing merge gates as false proof.

## Problem

GitHub issue #325 reports a semantic gap in the current gate: a demo log with execution failure still passes because the gate only verifies that `demo-output.log` exists in the diff.

Concrete evidence:

1. `.github/workflows/commitlint.yml` (`demo-gate`) currently checks changed demo directories and requires `demo-output.log` presence, but does not inspect log content.
2. `scripts/check_demo_proof.sh` mirrors the same presence-only logic for local pre-commit.
3. `tests/unit/test_ci_demo_proof_gate.py` currently locks existence behavior but not success semantics.
4. FR-323 generated a `hello/demo-output.log` containing `Node greet failed` and still satisfied the gate shape check.

Result: the gate enforces artifact shape, not artifact truth (`detection_without_enforcement`).

## Research: Existing Patterns and Prior Art

1. **Current gate behavior is explicitly presence-only.**
   - `.github/workflows/commitlint.yml` (`demo-gate`, “Verify demo output logs exist”)
   - `scripts/check_demo_proof.sh`

2. **Parity between CI and pre-commit is an existing contract.**
   - REQ-YG-200/CAP-79 describe identical changed-demo detection logic between CI job and pre-commit hook.

3. **No semantic validation tests exist today.**
   - `tests/unit/test_ci_demo_proof_gate.py` asserts missing-log failures and hook wiring, but not failed-log rejection.

4. **Failure markers are observable in committed logs.**
   - Example: `examples/demos/hello/demo-output.log` includes `[ERROR] ... Node greet failed`.

5. **Topic source file requested by prompt is absent in this worktree.**
   - Requested: `.chaplain/processing/gh-325.md`
   - Canonical planning source used: GitHub issue #325

## Objectives

1. Reject changed demo logs that show failed execution.
2. Reject changed demo logs that are empty or lack success evidence.
3. Preserve CI/pre-commit parity so local and remote enforcement cannot drift.

## Constraints

1. Keep scope to demo-proof gate surfaces and directly coupled tests/docs:
   - `.github/workflows/commitlint.yml`
   - `scripts/check_demo_proof.sh`
   - `tests/unit/test_ci_demo_proof_gate.py` (or a dedicated FR-325 test file)
   - requirement/capability docs that define REQ-YG-200 behavior
2. Do not run demos in CI; validation must remain log-based.
3. Preserve current changed-demo detection and feat/fix job gating behavior.
4. No relaxations of existing merge gates.

## Proposed Solution

### In scope

1. Keep existing “changed demo must include demo-output.log” checks.
2. Add log-content validation for each required log (CI and pre-commit):
   - Fail when fatal execution markers are present (for example: `Node .* failed`, `❌ Error:`, non-zero exit-code markers).
   - Fail when log is empty/whitespace-only.
   - Fail when no success evidence marker is present.
3. Define one shared marker contract used identically by CI and pre-commit (same regex set / same failure criteria).
4. Add focused unit coverage that proves:
   - failed log is rejected,
   - empty log is rejected,
   - successful log is accepted,
   - CI and pre-commit use equivalent semantics.

### Out of scope

1. Rewriting historical demo logs unrelated to the changed demo in a PR.
2. Provider/auth reliability fixes (this FR only validates proof artifacts).
3. Running live model calls in CI.

## Acceptance Criteria

- [x] **AC-01:** `demo-gate` still fails when a changed demo is missing `demo-output.log`.
- [x] **AC-02:** `demo-gate` fails when a changed `demo-output.log` contains fatal execution markers.
- [x] **AC-03:** `demo-gate` fails when a changed `demo-output.log` is empty or has no success evidence marker.
- [x] **AC-04:** `scripts/check_demo_proof.sh` enforces the same content rules locally as CI.
- [x] **AC-05:** Unit tests cover AC-02..AC-04 with explicit passing/failing fixtures.
- [x] **AC-06:** REQ-YG-200/CAP-79 wording is updated to reflect semantic validation (not only log presence).

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr325_demo_gate_log_content_validation.py`

Planned RED tests:

1. `test_ac02_ci_gate_script_contains_fatal_log_markers_check`
2. `test_ac03_ci_gate_script_rejects_empty_or_no_success_log`
3. `test_ac04_precommit_script_rejects_failed_demo_log`
4. `test_ac04_precommit_script_rejects_empty_demo_log`
5. `test_ac04_precommit_and_ci_share_same_semantic_rules`

RED command:

```bash
pytest tests/unit/test_fr325_demo_gate_log_content_validation.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
rg -n "Node .* failed|❌ Error:|exit code [1-9]|empty.*demo-output\\.log|success evidence" .github/workflows/commitlint.yml scripts/check_demo_proof.sh
```

## Alternatives Considered

1. **Keep presence-only gate**
   Rejected: does not enforce successful execution; repeats issue #325 failure mode.

2. **Run all changed demos in CI**
   Rejected: provider credentials and nondeterministic model outputs make this unreliable and out of current gate scope.

3. **Validate only in CI (skip pre-commit parity)**
   Rejected: delays feedback and violates existing CI/local parity contract for demo-proof enforcement.

## Related

- GitHub issue #325: <https://github.com/sheikkinen/yamlgraph/issues/325>
- `.github/workflows/commitlint.yml` (`demo-gate`)
- `scripts/check_demo_proof.sh`
- `tests/unit/test_ci_demo_proof_gate.py`
- `capabilities/CAP-79-demo-proof-gate.yaml`
- `ARCHITECTURE.md` (REQ-YG-200)
- `feature-requests/FR-206-demo-proof-gate.md`
- `feature-requests/FR-323-vertex-gemini-31-hello-smoke.md`
- Topic source requested: `.chaplain/processing/gh-325.md` (not present in this worktree)
