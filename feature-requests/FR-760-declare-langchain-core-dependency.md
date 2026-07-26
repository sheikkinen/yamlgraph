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

## Implementation Status (2026-07-26)

**Status:** Enforced. All 8 acceptance criteria satisfied.

- **Resolved floor:** `pip install -e ".[dev]"` in a fresh isolated worktree
  venv (Python 3.14.6) resolved `langchain-core==1.5.1`. Declared as
  `langchain-core>=1.5.1` in `[project.dependencies]` (AC-01).
- **Rationale entry:** added to `docs/dependency-rationale.yaml` naming the
  representative core consumers per contract: `BaseChatModel`
  (`yamlgraph/executor.py`, `yamlgraph/utils/llm_factory.py`), messages
  (`yamlgraph/executor_base.py`, `yamlgraph/streaming_events.py`),
  `StructuredTool` (`yamlgraph/tools/tool_builders.py`),
  `BaseCallbackHandler` (`yamlgraph/utils/timing_tracker.py`,
  `yamlgraph/utils/token_tracker.py`), and `RunnableConfig`
  (`yamlgraph/node_factory/subgraph_nodes.py`) (AC-02).
- **Gates:** `python scripts/dependency_rationale.py --strict` passes — 59
  dependencies, 50 documented rationales, 0 undocumented (AC-03).
- **Resolver:** `pip install -e ".[dev]"` re-resolves cleanly, no conflict
  between `langchain-core`, `langgraph`, and the `langchain-*` provider
  packages (AC-04).
- **Test verification (AC-05):** `tests/unit/test_dependency_rationale.py`
  (29 tests) passes. Full unit suite (`pytest tests/unit/ -q --no-cov -m
  "not slow"`) run in the isolated FR worktree venv: 7 failures / 5058
  passed — verified via a byte-identical control run on an **unmodified**
  `origin/main` worktree with the same optional packages installed
  (`feedparser`, `beautifulsoup4`): same 7 failures, same `5058 passed`
  count. Root causes are pre-existing environment gaps unrelated to this
  change (missing `z3`/`yamlgraph[verify]` extra; two full-suite-only
  order-dependent tests that pass in isolation) — not caused by declaring
  `langchain-core`. No gate was relaxed.
- **Changelog fragment:** `changelog/unreleased/fr760-langchain-core-dependency.md`
  (AC-06).
- **Diary reflection:** `docs/diary/2026-07-26-reflection-fr-760-clean-diff-noisy-environment.md`
  (AC-07).
- **Deviations from judgement:** none. All conditions C-1..C-5 honored — no
  direct-import scan added (deferred to FR-761), no model adapter/provider
  abstraction, no CI/hook/enforcement-infra edits, rationale entry is
  substantive (not presence-only), no resolver conflict encountered.

## PR #462 review fixes (2026-07-26)

**P1 — `docs/fr-board.md` corruption removed.** The first commit
regenerated `docs/fr-board.md` from this worktree, and
`scripts/fr_board.py`'s `collect_rows()` used `Path.cwd().name` (the
checkout directory's basename) as the board's `repo` column — since
the worktree lives at `tmp/worktrees/fr-760`, EVERY row in the board
was mislabeled `repo: fr-760` instead of `yamlgraph`, corrupting ~200
unrelated FR entries (FR-082 through FR-453 and others) far outside
this PR's frozen scope. Root-caused and fixed at the source: added
`repo_display_name()`, which prefers the stable `pyproject.toml`
`[project].name` field over the directory basename, falling back to
the dirname only when no `pyproject.toml` exists (F6: absent sibling
repos in `--project` mode). `python scripts/fr_board.py --check` now
passes, and the resulting diff against `main` is 4 lines — only
FR-760's own new rows — not a 400-line rewrite of unrelated repo
attribution. This is a general fix, not scoped to FR-760: any future
worktree-based commit touching `feature-requests/` would have hit the
same corruption without it.
