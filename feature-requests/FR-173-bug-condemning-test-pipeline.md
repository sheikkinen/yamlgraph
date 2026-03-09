# Feature Request: FR-173 Bug-Fix Pipeline with Condemning Test Phase

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-03-09

## Summary

Add a dedicated bug-fix pipeline to the Chaplain system that introduces a **Condemning Test** phase — a first-class step that reproduces the bug with a failing test before any fix is attempted. The existing Enforce phases (implement, test/demo, pre-commit, submit PR) follow after the bug is proven.

## Value Statement

Developers and the Inquisitor get a structured path from bug report to verified fix, ensuring every bug is condemned by a failing test before correction — turning Commandment 7 from aspiration into automated enforcement.

## Problem

The current Chaplain pipeline has two tracks:

1. **Plan → Judge** — transforms rough ideas into approved feature requests.
2. **Enforce** — implements approved FRs via TDD (RED → GREEN → REFACTOR).

Neither track is optimized for **bug fixing**. When a bug is reported (manually or via Inquisitor `--propose`), it enters the Plan → Judge pipeline as if it were a new feature. But bugs have a fundamentally different workflow:

- **Feature TDD**: RED means "write tests for behavior that doesn't exist yet."
- **Bug TDD**: RED means "prove the bug exists in the current codebase" — the condemning test must fail against the **unchanged** code before any fix is attempted.

Today, the Enforce pipeline's implement phase bundles test-writing and fixing together. There is no gate that verifies "this test fails on the current code" before the fix is applied. A developer (or agent) can accidentally write a test that passes without the fix, producing a false green — a hypothesis, not a proof (Commandment 7).

## Proposed Solution

### New Pipeline: Condemn → Fix → Verify → Submit

Extend the Chaplain system with a **bug-fix graph** that inserts a Condemning Test phase before the existing Enforce phases.

```yaml
# examples/bugfix/graph.yaml
metadata:
  name: bugfix-pipeline
  description: "Bug-fix pipeline: condemn → fix → verify → submit"

nodes:
  condemn:
    type: copilot
    prompt: prompts/condemn.yaml
    timeout: 1200
    state_key: condemn_result
    description: "Write condemning test; verify it FAILS on current code"

  fix:
    type: copilot
    prompt: prompts/fix.yaml
    timeout: 1800
    state_key: fix_result
    resume: "{state.condemn_result.session_id}"
    description: "GREEN: minimal fix to make condemning test pass"

  verify:
    type: copilot
    prompt: prompts/verify.yaml
    timeout: 900
    state_key: verify_result
    resume: "{state.condemn_result.session_id}"
    description: "Run full test suite + pre-commit hooks"

  submit:
    type: copilot
    prompt: prompts/submit-pr.yaml
    timeout: 500
    state_key: pr_result
    resume: "{state.condemn_result.session_id}"
    description: "Commit fix(scope): FR-XXX and create PR"
```

### Condemn Phase Contract

The `condemn` prompt enforces a strict protocol:

1. **Read** the bug report / FR (understand the failure).
2. **Write** one or more test functions tagged `@pytest.mark.req("REQ-YG-XXX")` that exercise the buggy behavior.
3. **Run** `pytest tests/unit/<test_file>.py -v --no-cov` against the **unmodified** codebase.
4. **Assert failure**: If the test passes, the bug is not proven — revise or abort.
5. **Commit RED**: `SKIP=pytest git commit -m "test(scope): FR-XXX condemning test for <bug>"` (RED commit, tests intentionally fail; `SKIP=pytest` preserves linting hooks while bypassing the test runner).

The condemning test commit is the proof trail. It must fail before the fix and pass after.

### Integration with watch.sh

Extend `watch.sh` to detect bug-type FRs and route them to the bug-fix graph instead of the feature enforce graph:

```bash
# In watch.sh, after detecting new_fr:
if grep -q 'Type.*Bug' "$new_fr"; then
    nohup scripts/bugfix_worktree.sh "$new_fr" > "tmp/bugfix-$(date +%s).log" 2>&1 &
else
    nohup scripts/enforce_worktree.sh "$new_fr" > "tmp/enforce-$(date +%s).log" 2>&1 &
fi
```

### Alternative: Single Enforce Graph with Conditional Phase

Instead of a separate graph, add a conditional `condemn` phase at the start of the existing enforce graph that activates when `Type: Bug` is detected in the FR:

```yaml
# In examples/enforce/graph.yaml
nodes:
  condemn:
    type: copilot
    prompt: prompts/condemn.yaml
    condition: "'Bug' in fr_type"
    state_key: condemn_result

  implement:
    type: copilot
    prompt: prompts/enforce-implement.yaml
    state_key: implement_result
    resume: "{state.condemn_result.session_id}"  # if condemn ran, resume its session
```

This avoids a separate script and graph but couples bug and feature workflows.

## Acceptance Criteria

- [ ] `examples/bugfix/graph.yaml` defines a 4-phase pipeline: condemn → fix → verify → submit
- [ ] Condemn phase prompt enforces: write test → run against unmodified code → assert failure
- [ ] Condemn phase aborts (or loops) if the condemning test passes on current code
- [ ] Fix phase resumes the condemn session and makes the minimal change to pass the test
- [ ] Verify phase runs full `pytest` suite and `pre-commit` hooks
- [ ] Submit phase creates a conventional commit with `fix(scope): FR-XXX` format
- [ ] `watch.sh` routes `Type: Bug` FRs to the bug-fix pipeline
- [ ] `scripts/bugfix_worktree.sh` creates an isolated worktree (mirrors `enforce_worktree.sh`)
- [ ] RED commit (condemning test) and GREEN commit (fix) are separate in git history
- [ ] Tests added for any new Python utilities supporting the pipeline
- [ ] Documentation updated in `examples/bugfix/README.md`

## Alternatives Considered

### 1. Separate process (dedicated `bugfix_worktree.sh` + graph)

**Pros:** Clean separation of concerns; bug-fix prompts can be specialized without bloating enforce prompts; independent evolution of the two pipelines.

**Cons:** Duplicates worktree setup logic; two graphs to maintain.

**Verdict:** Preferred. The condemn phase has fundamentally different constraints (test must fail on unmodified code) that don't map cleanly onto the feature enforce flow. Mitigate duplication by extracting shared worktree setup into a common function sourced by both scripts.

### 2. Extension of existing watch.sh + enforce graph

**Pros:** No new files; reuses existing infrastructure; conditional phase keeps everything in one place.

**Cons:** Couples bug and feature workflows; conditional logic in YAML graphs adds complexity; the `resume_from` chain becomes ambiguous when the condemn phase is skipped.

**Verdict:** Viable for a minimal first iteration, but risks growing the enforce graph beyond its current clean 4-phase structure.

### 3. No pipeline change — document the pattern

**Pros:** Zero code; just describe the condemning test discipline in `reference/`.

**Cons:** No enforcement; relies on developer discipline; Commandment 7 remains aspirational for bugs.

**Verdict:** Rejected. The whole point of the Chaplain pipeline is to automate discipline. Documentation alone contradicts the Scripture's enforcement philosophy.

## Related

- **Commandment 7** (CLAUDE.md): "No bug shall be fixed unless first condemned by a failing test."
- **FR-106**: Parallel Worktree Pipeline (established the enforce graph pattern)
- **FR-128**: YAMLGraphication of Enforcer (migrated enforce to graph.yaml)
- **FR-118/FR-126**: Inquisitor Auto-Propose (generates bug reports that would enter this pipeline)
- **Rite of Correction** (CLAUDE.md): "Write the failing test first. Correct the root cause second."
- `scripts/enforce_worktree.sh`: Template for `bugfix_worktree.sh`
- `examples/enforce/graph.yaml`: Template for `examples/bugfix/graph.yaml`

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Evaluated 2026-03-09 by Chaplain Judge.**

**Strengths:**
1. **Architecturally aligned.** All infrastructure is in place: `type: copilot` nodes (FR-081), worktree isolation (FR-106), session continuity (FR-105), and `watch.sh` routing. No new node types or framework extensions required.
2. **Clean single responsibility.** Despite touching multiple files (graph, prompts, script, watch.sh), every element serves one coherent concern: routing bug FRs through a condemn-first pipeline.
3. **Strong doctrinal grounding.** Directly enforces Commandment 7 and the Rite of Correction. Alternatives analysis is thorough — the choice of separate graph over conditional phase is well-justified.
4. **Proven template.** The enforce pipeline is a battle-tested 4-phase copilot graph. Copying and adapting it is low-risk.

**Corrections applied during judgement (non-blocking):**
1. **`--no-verify` → `SKIP=pytest`**: The RED commit step proposed `git commit --no-verify`, which violates the Scripture's explicit prohibition. Corrected to `SKIP=pytest git commit -m "..."` per CLAUDE.md doctrine — this preserves linting hooks while bypassing only the test runner.
2. **`resume_from:` → `resume:`**: The proposed YAML used a non-existent `resume_from:` field with raw state keys. Corrected to `resume: "{state.condemn_result.session_id}"` matching the proven pattern in `examples/enforce/graph.yaml` where all downstream phases share the first phase's session.

**Scope boundary (frozen):**
- **IN:** `examples/bugfix/graph.yaml`, 4 condemn/fix/verify/submit prompts, `scripts/bugfix_worktree.sh`, `watch.sh` Type-based routing, `examples/bugfix/README.md`, tests for new utilities.
- **OUT:** Modifications to existing enforce pipeline, new node types, Inquisitor integration changes, alternative 2 (conditional phase in enforce graph).
