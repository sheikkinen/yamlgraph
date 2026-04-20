# Feature Request: FR-260 Acceptance Tests Before Enforce

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-04-20

## Summary

Move worktree creation from the enforce phase into the plan-judge loop, and add a dedicated acceptance test generation step between research and judge. Judge evaluates the FR, the research brief, AND concrete failing tests — three inputs instead of two. Enforce receives a worktree with pre-committed RED tests and a clear contract: "make these tests pass."

## Value Statement

Pipeline operators get independent verification that acceptance criteria are testable before enforcement begins, eliminating the fox-guarding-henhouse problem where tests and code emerge from the same agent session.

## Problem

The current enforce pipeline writes tests alongside implementation in a single agent session. This creates three problems:

1. **No independent testability gate.** If acceptance criteria are vague or untestable, this is only discovered during enforce — after worktree creation, branch setup, and LLM context investment. Judge currently evaluates testability in the abstract ("are acceptance criteria measurable?") without proof.

2. **Late worktree creation.** The worktree is created inside `scripts/enforce_worktree.sh` at line 144, after judge has already rendered its verdict. Acceptance tests need a worktree to live in — they belong in the feature branch, not on main.

3. **Enforce is underspecified.** The implement phase prompt says "write failing tests, implement, refactor" — but the agent decides which tests to write. This couples test design to implementation knowledge, weakening the TDD contract.

### Current flow

```
plan → research → judge → [create worktree] → enforce(implement + tests → test_and_demo → critique → finalize)
```

### Proposed flow

```
plan → research → [create worktree] → write_acceptance_tests → judge → enforce(implement to pass tests → ...)
```

## Judge Issue Resolutions

### Issue 1: FR commitment timing — RESOLVED

**Chosen: Stage A/B approach.** Delete the alternative.

The FR draft is committed to main by a `create_worktree` python node after research completes (Stage A). The worktree branches from that commit. Judge runs after acceptance tests are written, evaluating three artifacts (Stage B).

**Justification:** The FR draft commit to main is harmless — it's a file in `.chaplain/drafts/`, not in `feature-requests/`. If judge AMENDs, the draft is moved back to inbox on main. If judge REJECTs, the draft is moved to `feature-requests/` with Rejected status. The worktree is cleaned up in either case. This preserves the invariant: worktrees always branch from a commit containing the FR.

**Rejected alternative:** Judge running inside the worktree. This requires changing judge's working directory, complicating session management and breaking the principle that judge evaluates from the main branch.

### Issue 2: `worktree_dir` in graph state — RESOLVED

Add `worktree_dir: str` and `branch: str` to the graph's `state:` block. A `create_worktree` python node computes both via existing helpers (`derive_branch_name()`, `construct_worktree_path()`) and returns them as state. The `write_acceptance_tests` node receives `worktree_dir` via `{state.worktree_result.worktree_dir}`.

### Issue 3: Worktree creation mechanism — RESOLVED

Create a new python tool at `.chaplain/lib/worktree.py` with a `create_worktree()` function. Add a `create_worktree` python node to the copilot graph. No new shell script; no modification to `watch.sh` orchestration.

The python tool:
1. Reads the FR draft path from `{state.drafts_dir}`
2. Commits the FR draft to main (`git add` + `git commit --no-verify`, mirroring `enforce_worktree.sh` line 80)
3. Calls `derive_branch_name()` to compute branch name
4. Calls `construct_worktree_path()` to compute worktree path
5. Runs `git worktree add`
6. Symlinks `.venv` and validates health (FR-174)
7. Returns `{"worktree_dir": "...", "branch": "..."}` to state

This keeps the unified graph model intact — same pattern as the existing `write_diary` python tool handling file I/O.

### Issue 4: Integration test specification — RESOLVED

Added AC-13 through AC-16 specifying:
- Unit test for `create_worktree` tool (valid output from FR path)
- Unit test for `write_acceptance_tests` prompt template (valid pytest structure)
- Integration test for pipeline ordering invariant (edge verification)
- Integration test for judge criterion 8 (test evidence evaluation)

## Proposed Solution

### 1. Add `create_worktree` python tool and node

**New tool `.chaplain/lib/worktree.py`:**

```python
def create_worktree(state: dict) -> dict:
    """Commit FR draft to main and create worktree for acceptance tests.

    Uses existing helpers from yamlgraph.utils.worktree_helpers.
    Returns worktree_dir and branch as state update.
    """
    from yamlgraph.utils.worktree_helpers import (
        construct_worktree_path,
        derive_branch_name,
        validate_venv_health,
        validate_venv_symlink,
    )
    # 1. Find FR draft in drafts_dir
    # 2. Commit FR draft to main (--no-verify)
    # 3. Derive branch and worktree path
    # 4. git worktree add -b <branch> <worktree_dir> main
    # 5. Symlink .venv, validate health (FR-174)
    return {"worktree_dir": worktree_dir, "branch": branch}
```

**Graph state additions:**

```yaml
state:
  # ... existing fields ...
  worktree_dir: str      # Path to feature worktree (output of create_worktree)
  branch: str            # Git branch name for worktree (output of create_worktree)
```

**Graph tool and node:**

```yaml
tools:
  # ... existing tools ...
  create_worktree_tool:
    type: python
    path: .chaplain/lib/worktree.py
    function: create_worktree

nodes:
  # Between research and write_acceptance_tests
  create_worktree:
    type: python
    tool: create_worktree_tool
    state_key: worktree_result  # Contains {worktree_dir, branch}
```

### 2. Add `write_acceptance_tests` copilot node

```yaml
# Stage 3b: Write Acceptance Tests
# Reads FR acceptance criteria, generates pytest tests, commits RED
write_acceptance_tests:
  type: copilot
  prompt: write-acceptance-tests
  backend: cli
  cli_flags:
    allow_all_paths: true
    allow_all_tools: true
    resume: "{state.plan_result.session_id}"
  variables:
    drafts_dir: "{state.drafts_dir}"
    worktree_dir: "{state.worktree_result.worktree_dir}"
    branch: "{state.worktree_result.branch}"
  state_key: acceptance_tests_result
  timeout: 600
```

**New prompt `.chaplain/graphs/copilot/prompts/write-acceptance-tests.yaml`:**

The prompt instructs the copilot to:
1. Read the FR's acceptance criteria from the draft in `{drafts_dir}`
2. Generate pytest test functions with `@pytest.mark.req("REQ-YG-XXX")` tags
3. Write tests to the worktree at `{worktree_dir}` (e.g., `{worktree_dir}/tests/unit/test_fr_XXX.py`)
4. Run the tests in the worktree to confirm they fail (RED)
5. Commit the RED tests in the worktree: `test(FR-XXX): RED acceptance tests`

### 3. Update judge prompt with test evidence

Add an 8th evaluation criterion to `.chaplain/graphs/copilot/prompts/judge.yaml`:

```yaml
8. Do the acceptance tests in the worktree compile and fail for the right reasons?
   If tests cannot be written from the acceptance criteria, the FR is underspecified.
   If tests fail for import errors or missing fixtures (not missing implementation), AMEND.
```

Judge now evaluates three artifacts: the FR, the research brief, and the failing test suite.

### 4. Update enforce implement prompt

Update `.chaplain/graphs/enforce/prompts/enforce-implement.yaml` to reference existing RED tests:

```
Acceptance tests already exist in the worktree (committed as RED).
Your job: make them pass with the minimal implementation, then refactor.
Do NOT modify the acceptance test assertions — they are the contract.
You may add additional tests for edge cases discovered during implementation.
```

### 5. Update `scripts/enforce_worktree.sh`

Modify to accept an optional pre-existing worktree path as a third argument:
- If worktree exists at the path: skip `git worktree add` and `.venv` symlink (lines 140-158)
- If worktree does not exist: retain current creation logic (direct `enforce_worktree.sh` invocations still work without the copilot pipeline)
- Remove FR commit logic (lines 77-83) when worktree is pre-existing (already committed by copilot graph)
- Retain cleanup trap, `cd`, and enforce graph invocation

### 6. Update edges

```yaml
edges:
  - from: START
    to: plan
  - from: plan
    to: research
  - from: research
    to: create_worktree          # NEW (FR-260)
  - from: create_worktree
    to: write_acceptance_tests   # NEW (FR-260)
  - from: write_acceptance_tests
    to: judge
  - from: judge
    to: summarize
  - from: summarize
    to: write_diary
  - from: write_diary
    to: END
```

## Acceptance Criteria

- [ ] **AC-01:** `worktree_dir: str` and `branch: str` are defined in the copilot graph state block
- [ ] **AC-02:** A `create_worktree` python node exists in `.chaplain/graphs/copilot/graph.yaml` between `research` and `write_acceptance_tests`
- [ ] **AC-03:** `create_worktree` python tool (`.chaplain/lib/worktree.py`) commits FR draft to main and creates worktree with `.venv` symlink
- [ ] **AC-04:** A `write_acceptance_tests` copilot node exists between `create_worktree` and `judge`
- [ ] **AC-05:** The `write-acceptance-tests.yaml` prompt reads FR acceptance criteria and generates pytest tests with `@pytest.mark.req` tags
- [ ] **AC-06:** Tests are committed as RED in the worktree before judge runs
- [ ] **AC-07:** Judge prompt includes criterion 8 evaluating test evidence
- [ ] **AC-08:** If acceptance tests cannot be written (criteria too vague), judge AMENDs the FR
- [ ] **AC-09:** Enforce implement prompt references existing RED tests instead of writing its own
- [ ] **AC-10:** `enforce_worktree.sh` accepts an optional pre-existing worktree path and skips creation when provided
- [ ] **AC-11:** Existing bugfix pipeline (`scripts/bugfix_worktree.sh`) is not affected
- [ ] **AC-12:** Pipeline timing metrics (FR-256) capture worktree setup duration in the new location
- [ ] **AC-13:** Unit test: `create_worktree` tool returns valid `worktree_dir` and `branch` from FR path
- [ ] **AC-14:** Unit test: `write-acceptance-tests.yaml` prompt template renders with valid variable substitution
- [ ] **AC-15:** Integration test: copilot graph edges enforce ordering plan → research → create_worktree → write_acceptance_tests → judge
- [ ] **AC-16:** Integration test: judge prompt contains criterion 8 text (test evidence evaluation)
- [ ] **AC-17:** Documentation updated (CLAUDE.md pipeline flow description)

## Alternatives Considered

### A. Generate tests without worktree (in-memory validation only)

Generate test code as text, include it in judge's evaluation, but don't commit until enforce. **Rejected:** Tests that aren't run aren't tests. The RED commit is proof that the test existed and failed before implementation.

### B. Judge writes the tests itself

Merge test generation into the judge phase. **Rejected:** Judge's role is evaluation, not creation. Separation of concerns — the author (plan) and critic (judge) should be distinct roles.

### C. Keep worktree creation in enforce, copy tests from main

Generate tests on main during plan-judge, then copy into the worktree at enforce start. **Rejected:** Tests on main that reference unimplemented features would fail CI. Tests belong in the feature branch from inception.

### D. Split copilot graph invocation in `watch.sh`

Run plan+research as one graph, shell operations for worktree, then judge as another graph. **Rejected:** Breaks the unified graph model. A python node within the graph handles shell operations cleanly (same pattern as `write_diary` tool).

## Related

- **FR-173** — Bug-Condemning Test Pipeline (same TDD-first principle for bugs)
- **FR-183** — Simplify Enforce Pipeline (current 4-node enforce structure)
- **FR-257** — Chaplain Research Step (research node this FR inserts after)
- **FR-106** — Parallel Worktree Pipeline (worktree creation mechanics)
- **FR-174** — Worktree venv corruption guard (cleanup logic preserved)
- **FR-256** — Pipeline timing metrics (phase tracking updated)
- **Commandment 7** — "No bug shall be fixed unless first condemned by a failing test"
- `scripts/enforce_worktree.sh` — Current worktree creation (lines 140-158)
- `.chaplain/graphs/copilot/graph.yaml` — Plan-Research-Judge pipeline
- `.chaplain/graphs/enforce/graph.yaml` — Enforce pipeline

## Judgement

**Verdict:** APPROVE
**Classification:** Framework primitive — restructures the core plan-judge-enforce pipeline; every `feat` FR gains independent testability; no competing framework implements this pattern.
**Date:** 2026-04-20
**Scope:** Frozen.

### Evaluation

1. **Scope: Clear and minimal.** Six coordinated changes (python tool, copilot node, judge criterion, enforce prompt, shell script, edges) are all necessary consequences of one architectural decision: move acceptance tests before judge. No orthogonal concerns bundled.

2. **No contradictions.** All 10 factual claims verified against codebase — line numbers, function signatures, node counts, edge structure, and cross-references are precise.

3. **Acceptance criteria: Measurable.** All 17 ACs are specific and testable. AC-13 through AC-16 define explicit unit and integration tests. AC-01 through AC-12 are structural/behavioral checks.

4. **Feasible.** All building blocks exist: python node pattern (`write_diary`), worktree helpers (7 functions), condemn prompt template (`bugfix-condemn.yaml`), session continuation (`resume:`). Estimated 3 days is realistic.

5. **Architecture-aligned.** Extends the copilot graph with established patterns. Strengthens TDD commitment (Commandment 7). The python tool in `.chaplain/lib/` follows the canonical `diary.py` pattern.

6. **Single responsibility.** Pipeline restructuring — each piece depends on the others.

7. **Alternatives well-analyzed.** Four alternatives considered and rejected with specific reasoning. No viable documentation-only solution exists.

### Annotations (non-blocking)

- **A1:** Section 5 originally referenced "backward-compatible for bugfix pipeline" — corrected. The bugfix pipeline uses `bugfix_worktree.sh` (separate script, AC-11), not `enforce_worktree.sh`. The retained behavior serves direct `enforce_worktree.sh` invocations, not the bugfix pipeline specifically.

- **A2:** AC-12 (timing metrics) has an implicit dependency on FR-256. If FR-256 is not yet implemented when FR-260 ships, AC-12 is vacuously satisfied. Implementer should verify FR-256 status and condition accordingly.

- **A3:** The `write_acceptance_tests` copilot node resumes the plan session (`{state.plan_result.session_id}`) but writes to the worktree (`{worktree_dir}`). The prompt must explicitly instruct the agent to `cd` to the worktree before writing files, or use absolute paths. Verify during implementation.

## Research Brief

*Generated 2026-04-20 by independent research agents. Sources: web docs, codebase grep, diary corpus.*

### Competitive Landscape

No competing agent framework separates test authoring from implementation as distinct pipeline steps. This is a novel pattern in the AI agent space.

| Framework | Test Capabilities | Test-First Gate | Source |
|---|---|---|---|
| **LangGraph** | pytest unit/integration | ❌ None | [docs](https://docs.langchain.com/oss/python/langgraph/overview) |
| **CrewAI** | pytest + `.env.test` config | ❌ None | [repo](https://github.com/crewAIInc/crewAI) |
| **AutoGen / MS Agent Framework** | pytest; Labs has experimental benchmarking | ⚠️ Post-execution only | [repo](https://github.com/microsoft/agent-framework) |
| **OpenAI Agents SDK** | pytest + Coverage.py | ❌ None | [docs](https://openai.github.io/openai-agents-python/) |
| **Google ADK** | `.test.json` evaluation files | ⚠️ Evaluates agent behavior, not generated code | [docs](https://google.github.io/adk-docs/) |
| **Cursor / Devin / Codex** | Proprietary; no public test-first workflow | ❌ None | N/A |
| **BDD/Cucumber** | Gherkin spec-first | ✅ Manual authoring, not agent-generated | Traditional |

**Closest external analog:** Google ADK's `.test.json` — defines expected trajectories before running, but validates agent behavior rather than generated code.
**Closest internal analog:** YAMLGraph's bugfix-condemn pattern (FR-173) — writes failing tests, commits RED, uses `@pytest.mark.req`. Direct template for `write_acceptance_tests`.

**Documenting vs. building:** No existing solution to document. The pattern is novel and internal — it requires pipeline restructuring, not documentation.

### Existing Abstractions

| Abstraction | Location | Lines | Overlap with FR-260 |
|---|---|---|---|
| Bugfix condemn prompt | `examples/bugfix/prompts/bugfix-condemn.yaml` | 1-47 | Writes failing tests, commits RED with `SKIP=pytest`, tags `@pytest.mark.req`. Direct template for `write-acceptance-tests.yaml`. |
| Copilot pipeline graph | `.chaplain/graphs/copilot/graph.yaml` | 1-109 | 5-node linear chain (plan → research → judge → summarize → write_diary). FR-260 inserts 2 nodes between research and judge. 8 state fields; FR-260 adds `worktree_dir` + `branch`. |
| Judge prompt | `.chaplain/graphs/copilot/prompts/judge.yaml` | 1-48 | 7 evaluation criteria. FR-260 adds criterion 8 (test evidence). Verdict options: APPROVE/AMEND/REJECT/SPLIT. |
| Enforce implement prompt | `.chaplain/graphs/enforce/prompts/enforce-implement.yaml` | 1-33 | Currently couples test writing to implementation: "RED → GREEN → REFACTOR" in same agent session. FR-260 decouples — enforce receives pre-committed RED tests. |
| Enforce pipeline graph | `.chaplain/graphs/enforce/graph.yaml` | 1-102 | 4-node chain (implement → test_and_demo → critique → finalize). All phases chain via session continuation (`resume:`). |
| Worktree helpers | `yamlgraph/utils/worktree_helpers.py` | 1-255 | All 7 functions exist: `derive_branch_name()` (L23), `construct_worktree_path()` (L43), `validate_clean_working_tree()` (L61), `validate_venv_health()` (L120), `validate_venv_symlink()` (L151), `clean_stale_pth_entries()` (L173), `validate_editable_install()` (L237). Creation logic is in shell, not yet Python. |
| enforce_worktree.sh | `scripts/enforce_worktree.sh` | 1-211 | FR commit at L75-83 (`git add` + `git commit --no-verify`). Worktree creation at L144 (`git worktree add`). Venv symlink + validation at L148-158. FR-260 moves creation to python node; shell accepts optional pre-existing worktree. |
| Write diary tool | `.chaplain/lib/diary.py` | 1-120 | Canonical pattern for python tools in graph nodes: `def write_diary(state: dict) -> dict:`. FR-260 replicates as `create_worktree(state)`. |
| Session continuation | Graph YAML `resume:` field | 5 files | Established pattern (FR-105). Research and judge resume plan's session. FR-260's `write_acceptance_tests` resumes the same session. |
| Python node type | `.chaplain/graphs/` | 14 instances | 2 in copilot graph, 12 in philosopher graph. FR-260 adds 1 (`create_worktree`). |

### Diary Precedents

| Entry | Trap / Pattern | Relevance to FR-260 |
|---|---|---|
| `2026-04-20-chaplain-as-compiler.md` | **IR Generation gap** | Directly names FR-260's problem: "Without intermediate representation (failing tests), enforce does parse-and-codegen in one pass." Acceptance tests are the IR. |
| `2026-04-20-reflection-fr-257.md` | **`unchallenged_premise`** — Judge validates execution, not intent | Warns that validation before enforcement can validate the *wrong thing*. Acceptance tests must be strategically correct, not just technically well-formed. FR-260 gives judge test evidence to catch underspecified criteria. |
| `2026-04-18-reflection-fr-236.md` | **`downstream_symptom_fix`** | Early worktree creation can leave stale metadata. "Stale metadata is worse than missing metadata." Cleanup must apply to both old and new worktree timing. |
| `2026-03-09-reflection-FR-173.md` | **`stalled_agent_recovery`** | FR-173 (bugfix condemn) is the direct ancestor. Shows how partial work can be recovered via test inventory — applies to partial acceptance test suites during enforce. |
| `2026-03-09-reflection-fr-175.md` | **`parallelism_theatre`** | Sequential enforcement prevents race conditions on shared bookkeeping files. Acceptance test runs must serialize. "When writes touch shared files, serialize at the orchestration layer." |
| `2026-04-19-reflection-fr-241.md` | **CAP/REQ-YG parallel collision** | Early worktree creation must coordinate ID assignment before enforcement branches diverge. Automate next-free ID lookup at branch creation, not post-hoc. |
| `2026-04-20-reflection-fr-256.md` | **`infrastructure_self_exempt`** | AC-12 requires timing metrics for the new worktree-setup phase. "Instrument the instrumenter" — acceptance test pipeline must expose p95 duration. |

### Usage Evidence

| Metric | Count | Source |
|---|---|---|
| Copilot nodes (`type: copilot`) | **65 instances across 15 files** | `grep -r "type: copilot" *.yaml` |
| Python nodes (`type: python`) | **333 instances across 62 files** | `grep -r "type: python" *.yaml` |
| Worktree references | **41 files** (.py, .sh, .yaml) | `grep -r "worktree"` |
| `@pytest.mark.req` usage | **276 files** | `grep -r "pytest.mark.req" *.py` |
| TDD/test-first feature requests | **27 FRs** | `grep -rl "TDD\|test-first\|failing test\|condemn" feature-requests/` |
| `resume:` session continuations | **5 files** | `grep -r "resume:" *.yaml` |
| `enforce_worktree.sh` references | **22 files** | Cross-reference .sh, .py, .yaml |
| Chaplain pipeline graphs | **3** | copilot, enforce, philosopher |
| Real-world use cases beyond proposal | Every `feat` FR processed by Chaplain gains independent testability; 27 FRs reference TDD | — |

### Classification Signal

- **Abstraction level:** **primitive** — restructures the core plan-judge-enforce pipeline (3 graphs, 22 referencing files)
- **Recommended approach:** **build** — no external solution exists to document; internal condemn pattern (FR-173) provides template; all worktree helpers already exist in Python
- **Key risk:** Python node performing git operations (commit + worktree add) within the graph must preserve the invariant that worktrees branch from a commit containing the FR; early worktree creation expands the cleanup surface (diary: `downstream_symptom_fix`, `stalled_agent_recovery`)
