# Feature Request: FR-698 — Executor-Neutral Worktree Tooling (`wt`)

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-07-07

## Summary

Create one shared worktree lifecycle command (`scripts/worktree.sh`) and make watcher wrappers plus `scripts/copilot_instrument.sh` delegate to it, so manual and chaplain paths use the same create/list/remove behavior and self-heal safeguards.

## Value Statement

Operators get a fast isolated-work lane with the same incident-hardened teardown protections already used by watcher flows.

## Problem

Worktree lifecycle logic is split across three independent implementations:

1. `.chaplain/lib/watcher/worktree_setup.sh` + `worktree_teardown.sh`
2. `scripts/copilot_instrument.sh`
3. `.chaplain/scripts/clean-worktree.sh`

This duplicates behavior and hides critical safeguards in watcher-only teardown:

- `core.bare=true` recovery (FR-139)
- stale `.pth` cleanup (FR-174)
- editable install revalidation/self-heal (FR-241)
- merged-PR branch collision guard in setup (FR-275)

At the same time, pre-command guard (FR-662) denies branch creation in main worktree but currently does not point to the manual isolated-work lane that is already allowed via worktrees.

## Research

### Existing code paths

- `.chaplain/lib/watcher/worktree_setup.sh`
  - derives branch/worktree from topic
  - prunes stale worktree metadata
  - guards against merged-PR branch reuse via `gh pr list`
  - emits JSON envelope keys: `wt_dir`, `wt_branch`, `main_dir`, `work_dir`
- `.chaplain/lib/watcher/worktree_teardown.sh`
  - removes worktree/branch refs
  - restores `core.bare=false` when corrupted
  - runs `clean_stale_pth_entries(...)`
  - validates editable install and self-heals with `pip install -e`
- `scripts/copilot_instrument.sh`
  - uses private `git worktree add --detach ...` and private cleanup trap
- `.chaplain/scripts/clean-worktree.sh`
  - issue-number-specific cleanup path, separate from watcher setup/teardown guards
- `.github/hooks/scripts/pre-command-guard.sh`
  - denies `git checkout -b` / `git switch -c` / `git branch <name>` in main worktree
  - denial text currently points only to chaplain inbox flow

### Prior requirements and tests

- `REQ-YG-106` (CAP-33): worktree lifecycle derivation/orchestration baseline
- `REQ-YG-156` (CAP-60): venv corruption and stale `.pth` guard
- `REQ-YG-244` (CAP-102): teardown editable-install self-heal
- Existing tests to extend:
  - `.github/hooks/tests/test_pre_command_guard.py`
  - `tests/unit/test_worktree_venv_guard.py`
  - `tests/unit/test_worktree_teardown_self_heal.py`
  - `tests/integration/test_worktree_integration.py`

## Objectives

1. Single source of truth for lifecycle verbs in `scripts/worktree.sh`: `new`, `spike`, `list`, `rm`.
2. Keep watcher FSM behavior unchanged by converting watcher setup/teardown scripts to wrappers.
3. Make `scripts/copilot_instrument.sh` delegate to shared lifecycle commands.
4. Update FR-662 denial guidance to include manual isolated-work command.

## Constraints

1. No watcher FSM state/transition changes.
2. Preserve existing self-heal behavior from REQ-YG-156 and REQ-YG-244.
3. No new dependencies.
4. Keep scope to worktree lifecycle tooling; do not expand into general git workflow management.

## Proposed Solution

### Canonical command and invocation contract

- Add executable `scripts/worktree.sh` as canonical interface.
- Add executable alias `scripts/wt` as a thin wrapper that execs `scripts/worktree.sh`.
- Tests invoke canonical form (`bash scripts/worktree.sh <verb> ...`) to avoid PATH/alias variance.
- Canonical command options needed by existing watcher call sites:
  - `new <name> [--prefix <branch_prefix>] [--work-dir <selector>] [--json]`
  - `spike <name> [--prefix <branch_prefix>] [--work-dir <selector>] [--json]`
  - `rm <name|--dir <wt_dir>> [--note "<text>"]`
  - `list`

### Lifecycle verbs

- `scripts/worktree.sh new <name>`
  - create `tmp/worktrees/feat/<name>` (deterministic path)
  - create branch from `main`
  - apply merged-PR collision guard
  - symlink `.venv` from main worktree
- `scripts/worktree.sh spike <name>`
  - same creation flow as `new`
  - mark worktree as spike via marker file `.wt-spike-meta.json` in the worktree root
- `scripts/worktree.sh list`
  - print worktree path, branch, and age
- `scripts/worktree.sh rm <name> [--note "what was learned"]`
  - remove worktree + branch refs
  - run teardown self-heal sequence (FR-139/174/241 behavior)
  - if target is a spike worktree, enforce spike note contract before removal

### Spike artifact contract

- For spike-marked worktrees, `rm` requires `--note "<text>"`.
- `--note` must be a single non-empty line with at least 10 non-whitespace characters.
- On success, append one line to `docs/diary/spike-notes.log`:
  - format: `YYYY-MM-DD <name>: <note>`
- If `docs/diary/spike-notes.log` does not exist, create it before appending.
- Missing/invalid note is a hard failure (exit non-zero, no removal performed).

### Wrapper/delegation wiring

1. `.chaplain/lib/watcher/worktree_setup.sh` becomes a wrapper around `scripts/worktree.sh new` with explicit translation:
   - `topic_basename=$(basename "$TOPIC_FILE" .md)` (current behavior preserved)
   - call `scripts/worktree.sh new "$topic_basename" --prefix "$BRANCH_PREFIX" --work-dir "$WORK_DIR" --json`
   - canonical command computes:
     - `wt_branch="${BRANCH_PREFIX}${name}"`
     - `wt_dir="tmp/worktrees/${wt_branch}"` when `work_dir="."`
     - `wt_dir="tmp/worktrees/${work_dir_slug}/${wt_branch}"` when `work_dir!="."`
   - wrapper passes through canonical JSON unchanged so stdout contract remains exactly `wt_dir`, `wt_branch`, `main_dir`, `work_dir`.
2. `.chaplain/lib/watcher/worktree_teardown.sh` becomes wrapper around `scripts/worktree.sh rm --dir "$WT_DIR"` (keep existing `--dir` caller contract, move lifecycle logic into canonical command).
3. `scripts/copilot_instrument.sh` delegates create/remove to `scripts/worktree.sh`.
4. `.github/hooks/scripts/pre-command-guard.sh` denial text adds:
   - `For isolated manual work: scripts/worktree.sh new <name>`

### Implementation sequence (authority gate)

1. RED commit first: add the three new test modules listed in "Failing Acceptance Tests" and run the RED command set. Expected failure reason: missing canonical worktree tooling/wrappers, not test harness/import errors.
2. Add capability YAML files and ARCHITECTURE requirement rows for new REQ IDs.
3. Implement canonical script and wrappers.
4. Re-run tests and migrate status to Judged/In Progress during enforcement.

## Acceptance Criteria

- [x] `scripts/worktree.sh` provides `new`, `spike`, `list`, `rm` and usage output.
- [x] `scripts/wt` exists and delegates to `scripts/worktree.sh`.
- [x] `rm` executes teardown self-heal sequence equivalent to current watcher teardown:
  - restore `core.bare=false` if corrupted
  - clean stale `.pth` references
  - validate and self-heal editable install
- [x] Watcher setup wrapper preserves stdout JSON envelope contract exactly:

| Field | Meaning |
|---|---|
| `wt_dir` | Created worktree directory path |
| `wt_branch` | Created branch name |
| `main_dir` | Main repository root path |
| `work_dir` | Caller-provided work-dir selector |

- [x] `scripts/copilot_instrument.sh` no longer contains private lifecycle `git worktree add/remove` logic.
- [x] FR-662 deny reason text includes `scripts/worktree.sh new <name>`.
- [x] Branch-create deny/allow behavior remains unchanged (text update only).
- [x] Spike teardown enforces note contract; invalid/missing note aborts removal.
- [x] If `docs/diary/spike-notes.log` is absent, `rm --note` creates it before appending.

## Implementation Status (2026-07-07)

- Implemented canonical `scripts/worktree.sh` with `new|spike|list|rm` verbs and `scripts/wt` alias.
- Converted watcher setup/teardown scripts into wrappers over canonical commands while preserving setup JSON contract.
- Updated `scripts/copilot_instrument.sh` to delegate create/remove lifecycle to canonical worktree tooling.
- Updated pre-command guard deny guidance to include manual isolated-work command.
- Added CAP-189..192 and regenerated `ARCHITECTURE.md` generated capability section.
- Added FR-698 acceptance tests and requirement markers for new REQ IDs.

## Failing Acceptance Tests (RED before implementation)

1. `tests/unit/test_worktree_cli_red.py`
   - `test_worktree_usage_lists_new_spike_list_rm`
   - `test_worktree_alias_executes_canonical_script`
   - `test_worktree_rm_runs_self_heal_sequence`
   - `test_worktree_spike_rm_requires_note_and_blocks_without_it`
   - `test_worktree_spike_rm_appends_spike_note_log_line`
2. `tests/unit/test_watcher_worktree_wrapper_red.py`
   - `test_worktree_setup_wrapper_preserves_json_contract_keys`
   - `test_worktree_teardown_wrapper_delegates_to_worktree_rm`
3. `tests/unit/test_copilot_instrument_worktree_delegation_red.py`
   - `test_instrument_script_calls_shared_worktree_new_rm`
   - `test_instrument_script_has_no_direct_worktree_add_remove`
4. `.github/hooks/tests/test_pre_command_guard.py`
   - extend branch-create deny assertion to require `scripts/worktree.sh new <name>` in deny reason text

RED command set:

```bash
pytest -q .github/hooks/tests/test_pre_command_guard.py
pytest -q tests/unit/test_worktree_cli_red.py tests/unit/test_watcher_worktree_wrapper_red.py tests/unit/test_copilot_instrument_worktree_delegation_red.py
```

## Requirement Traceability Plan

Existing requirements reused:

- `REQ-YG-156` — stale `.pth`/venv guard expectations for teardown
- `REQ-YG-244` — editable install teardown self-heal
- `REQ-YG-106` — baseline worktree lifecycle derivation/orchestration

New requirement IDs to add during implementation:

- `REQ-YG-524` — canonical executor-neutral `scripts/worktree.sh` CLI contract (`new|spike|list|rm`) and `scripts/wt` alias wrapper
- `REQ-YG-528` — watcher wrapper JSON envelope contract preserved (`wt_dir`, `wt_branch`, `main_dir`, `work_dir`)
- `REQ-YG-526` — instrumentation script delegates worktree lifecycle to shared tooling (no private add/remove lifecycle)
- `REQ-YG-527` — pre-command guard branch-create denial guidance includes manual isolated-work lane command

Capability files to add (next available CAP IDs confirmed up to CAP-188 in repository):

- `capabilities/CAP-189-worktree-cli-contract.yaml` → `REQ-YG-524`
- `capabilities/CAP-193-watcher-wrapper-json-envelope.yaml` → `REQ-YG-528`
- `capabilities/CAP-191-instrument-worktree-delegation.yaml` → `REQ-YG-526`
- `capabilities/CAP-192-branch-deny-guidance-manual-worktree-lane.yaml` → `REQ-YG-527`

Architecture update plan:

- Add REQ-YG-524..527 rows to `ARCHITECTURE.md` requirements table during enforcement in the same change that introduces CAP-189..192 and RED tests.

Planned RED tests above must be tagged with the corresponding `@pytest.mark.req("REQ-YG-...")` markers.

## Alternatives Considered

1. Keep three implementations and only document usage.
   - Rejected: preserves drift and incident-relearning risk.
2. Expand only `.chaplain/scripts/clean-worktree.sh`.
   - Rejected: cleanup-only approach does not solve shared creation semantics.
3. Force all isolated work through chaplain pipeline.
   - Rejected: executor-neutral goal requires a direct manual lane.

## Non-goals

- No changes to watcher FSM states/transitions.
- No automatic PR/merge behavior for manual worktrees.
- No broader git branching policy changes beyond guidance text.

## Judge Notes

**2026-07-07 — AMEND**

FR is well-scoped with a real problem (confirmed: `copilot_instrument.sh` has private `git worktree add/remove` at lines 105 and 110; three independent lifecycle implementations verified to exist). Classification: **Framework primitive** — 3+ use cases (manual operator lane, watcher FSM, instrumentation), no existing shared abstraction.

Four issues must be resolved before authority is granted:

### Issue 1: RED tests are absent (blocking)

The FR lists failing acceptance tests in section "Failing Acceptance Tests (RED before implementation)" but none of the three new test files exist in the worktree:

- `tests/unit/test_worktree_cli_red.py` — MISSING
- `tests/unit/test_watcher_worktree_wrapper_red.py` — MISSING
- `tests/unit/test_copilot_instrument_worktree_delegation_red.py` — MISSING

Commandment 7 mandates RED exists before GREEN. The enforce agent must write these tests first, confirm they fail for the correct reason (missing implementation, not import errors or fixture gaps), and commit the RED state before touching any production code.

### Issue 2: CAP YAML files for new REQ IDs not planned (blocking)

The FR declares four new requirement IDs (REQ-YG-524 through REQ-YG-527) but does not mention the corresponding `capabilities/CAP-XXX-name.yaml` files required by ADR-001. The capability registry is loaded dynamically from YAML — no capability file means the REQ IDs are phantom references that will fail `changelog-req-gate` CI. Add to the implementation plan:

- `capabilities/CAP-NNN-worktree-cli-contract.yaml` → REQ-YG-524
- `capabilities/CAP-NNN-watcher-wrapper-json-envelope.yaml` → REQ-YG-528
- `capabilities/CAP-NNN-instrument-delegation.yaml` → REQ-YG-526
- `capabilities/CAP-NNN-branch-deny-guidance.yaml` → REQ-YG-527

Assign the next available CAP numbers during implementation.

### Issue 3: Watcher wrapper translation contract underspecified (blocking)

`worktree_setup.sh` currently takes `--topic <topic_file>` and derives branch/path from the topic filename using a `BRANCH_PREFIX`. The FR says it becomes "a wrapper around `scripts/worktree.sh new`" but does not specify:

- How `--topic <file>` maps to the `<name>` argument of `scripts/worktree.sh new`
- Whether `BRANCH_PREFIX` is still honoured by the canonical command or dropped
- Whether `--work-dir` and `--branch-prefix` flags are forwarded to the canonical command or absorbed by the wrapper

The JSON envelope contract (`wt_dir`, `wt_branch`, `main_dir`, `work_dir`) must still be emitted on stdout. Specify in the "Proposed Solution" section how the wrapper captures the canonical command's output and re-emits the required JSON keys, or whether `scripts/worktree.sh new` itself emits a JSON envelope that the wrapper passes through.

### Issue 4: Spike log file first-run behaviour unspecified (minor)

The spike note contract appends to `docs/diary/spike-notes.log`. The behaviour when this file does not exist is unspecified. Clarify: the command must create the file on first use (not fail). Add one acceptance criterion line: "If `docs/diary/spike-notes.log` does not exist, `rm --note` creates it before appending."

---

**Status:** AMEND — address all four issues, then resubmit for re-judgement.

---

**2026-07-07 — APPROVE (re-judgement)**

All four blocking issues from the prior AMEND are resolved as planning artifacts in this revision:

1. **RED-first gate**: "Implementation sequence (authority gate)" now mandates RED commit (with three test modules listed by filename) as step 1 before any production edit. The tests are not yet written — that is the enforcer's first obligation, not a condition for authority. The FR correctly places the mandate inside the implementation sequence, not the acceptance criteria.

2. **CAP plan resolved**: CAP-189..192 pinned with exact filenames and REQ-YG-524..527 cross-references. No placeholder IDs remain.

3. **Wrapper translation contract**: Verified against actual `worktree_setup.sh` (lines 14–46, 100). The FR's specification matches the existing flag interface (`--topic`, `--branch-prefix`, `--work-dir`), path derivation logic, and JSON envelope exactly. Pass-through contract is explicit.

4. **Spike log first-run**: Acceptance criterion added ("If `docs/diary/spike-notes.log` is absent, `rm --note` creates it before appending."). Corresponding test (`test_worktree_spike_rm_appends_spike_note_log_line`) covers it.

**Classification confirmed**: Framework primitive — 3 use cases (manual operator lane, watcher FSM, copilot instrumentation). Problem verified real: `copilot_instrument.sh` contains private `git worktree add/remove` at lines 105 and 110.

**Scope**: Single responsibility (worktree lifecycle unification). No contradictions. Constraints preserve watcher FSM state machine unchanged. Acceptance criteria are measurable.

**Authority granted.** Enforcer must: (1) write RED tests and commit with `SKIP=pytest`; (2) add CAP-189..192 YAML files and ARCHITECTURE rows; (3) implement canonical script and wrappers; (4) confirm GREEN.

**Status:** APPROVED — 2026-07-07

## Planner Amendments (2026-07-07)

This draft addresses the four AMEND findings as planning artifacts:

1. **RED-first gate clarified**: added explicit implementation sequence requiring RED test modules/commands as step 1 before production edits.
2. **CAP plan resolved**: pinned concrete capability files `CAP-189..CAP-192` mapped to `REQ-YG-524..527` (no placeholder IDs).
3. **Wrapper translation contract specified**: documented exact mapping from watcher flags (`--topic`, `--branch-prefix`, `--work-dir`) to canonical `scripts/worktree.sh new ... --json`, including JSON pass-through contract.
4. **Spike log first-run behavior defined**: added requirement that `docs/diary/spike-notes.log` is created automatically when missing.

## Related

- Topic: `.chaplain/processing/executor-neutral-worktree-tooling.md`
- Setup: `.chaplain/lib/watcher/worktree_setup.sh`
- Teardown: `.chaplain/lib/watcher/worktree_teardown.sh`
- Instrumentation: `scripts/copilot_instrument.sh`
- Cleanup helper: `.chaplain/scripts/clean-worktree.sh`
- Hook guard: `.github/hooks/scripts/pre-command-guard.sh`
- Hook tests: `.github/hooks/tests/test_pre_command_guard.py`
- Requirements source: `ARCHITECTURE.md`, `capabilities/CAP-33-worktree-pipeline.yaml`, `capabilities/CAP-60-worktree-venv-corruption-guard.yaml`, `capabilities/CAP-102-complete-worktree-teardown-self-heal.yaml`
