# Feature Request: Declare langchain-core as Explicit Dependency

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-07-26
**First consumer / first event:** The dependency resolver on the next `pip install yamlgraph`, at the moment a future `langgraph` release changes its `langchain-core` pin and silently shifts the message/tool/callback contract YAMLGraph imports directly.

## Summary

`langchain_core` is imported directly by core modules and tests (messages, tools, callbacks, runnables, `BaseChatModel`) but arrives only transitively via `langgraph` and provider packages. Declare it explicitly in core dependencies with a rationale entry, making the effective runtime contract honest.

## Value Statement

Maintainers get a visible dependency diff when the most-imported foreign contract in the codebase changes version, instead of invisible drift through transitive resolution.

## Problem

From `docs/plan-research-dependency-negative-space.md` (direct-import table, ranked recommendation 2):

- The effective runtime contract is LangChain's `BaseChatModel`, message classes, callback types, and structured-output behavior — but no `langchain-core` pin exists in `pyproject.toml`.
- The Scripture's `the_one_law` demands normalization at the boundary where external data enters; a transitive dependency is a boundary nobody owns. This is the `module_structure` boundary class (FR-218): contracts must be declared, not assumed.
- Replacing any `langchain-*` provider today is medium-to-high cost because the implicit contract is undeclared.

## Ideal Result

`pyproject.toml` core dependencies name every package that core `yamlgraph/` modules import directly, each with a documented rationale; `langchain-core` version movements appear in dependency diffs and CI, never as ambient drift.

## Proposed Solution

1. Add `langchain-core>=<resolved-version>` to `[project.dependencies]`. Floor derivation rule (R-2): after the implementation environment resolves `pip install -e ".[dev]"`, record the resolved `langchain-core` version and use that exact resolved version as the minimum floor.
2. Add a substantive rationale entry to `docs/dependency-rationale.yaml` (R-3): non-empty `rationale`, `modules`, and `added` fields, where `modules` names representative core import consumers for message, tool, callback, runnable, and chat-model contracts. A placeholder that merely satisfies the script's presence check does not qualify.
3. Verify no resolver conflict with `langgraph` and provider extras (`pip install -e ".[dev]"` clean). If the resolver exposes a conflict, stop and amend the FR — do not widen scope into dependency-governance redesign.
4. Verify only the existing `scripts/dependency_rationale.py --strict` gate (R-1). This FR authorizes **no** new direct-import scan, governance gate, CI hook, or script behavior change — all direct-import enforcement belongs to FR-761.

Explicitly **not** in scope: a YAMLGraph-native model adapter contract (`YAMLGraphChatRequest`/`ProviderAdapter`). That is a major refactor with its own FR if ever pursued; this FR is the honesty fix that makes the implicit contract visible first.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `pyproject.toml` contains `langchain-core>=<resolved-version>` in core `[project.dependencies]`, where `<resolved-version>` is the exact version resolved in the implementation environment after `pip install -e ".[dev]"`
- [ ] AC-02: `docs/dependency-rationale.yaml` contains a `langchain-core` entry with non-empty `rationale`, `modules`, and `added` fields; `modules` names representative core import consumers for message, tool, callback, runnable, and chat-model contracts
- [ ] AC-03: `python scripts/dependency_rationale.py --strict` passes
- [ ] AC-04: `pip install -e ".[dev]"` resolves without dependency conflict
- [ ] AC-05: The targeted dependency/rationale checks and the unit suite pass without relaxing existing gates
- [ ] AC-06: A changelog fragment exists under `changelog/unreleased/` describing FR-760
- [ ] AC-07: A diary reflection exists under `docs/diary/` for the implementation
- [ ] AC-08: The FR is updated with implementation status, the resolved `langchain-core` version used as the floor, and any deviations from the judgement

## Alternatives Considered

- **Introduce a YAMLGraph-native model adapter boundary instead:** deferred — correct long-term direction per the research doc, but a major refactor; declaring the dependency is the minimal honest step and does not preclude the adapter later.
- **Leave transitive:** rejected — the package is imported by core modules; provider SDK churn is too fast for undeclared contracts.

## Related

- `docs/plan-research-dependency-negative-space.md` — direct-import table, finding 2, recommendation 2
- FR-218 module_structure boundary precedent
- Sibling FRs from the same research: FR-759, FR-761, FR-762

## Judgement (2026-07-26)

**Verdict:** APPROVED WITH REVISIONS — revisions R-1..R-4 folded above; authority active.

Full judgement: [FR-760-declare-langchain-core-dependency.judgement.md](FR-760-declare-langchain-core-dependency.judgement.md)

**Conditions (GATE):** C-1 no direct-import scan governance here — defer to FR-761; C-2 no native model adapter / provider abstraction / LangChain replacement surface; C-3 no edits to CI, hooks, judge/review doctrine, or enforcement infra; C-4 rationale entry must be substantive, not presence-check theatre; C-5 on resolver conflict, stop and amend the FR.

**Scope frozen:** D-1 `pyproject.toml` core dependency; D-2 substantive rationale entry; D-3 changelog fragment; D-4 diary reflection; D-5 FR implementation notes with resolved version decision.
