# Judgement: FR-760 Declare langchain-core as Explicit Dependency

**Verdict:** APPROVED WITH REVISIONS - the dependency-honesty fix is real and minimal, but authority activates only after the FR removes the direct-import guard ambiguity and makes the version/rationale acceptance criteria mechanically substantive.

**Reviewed against:** `feature-requests/FR-760-declare-langchain-core-dependency.md`; `docs/plan-research-dependency-negative-space.md`; `feature-requests/FR-218-import-linter-architectural-boundary-enforcement.md`; `pyproject.toml`; `docs/dependency-rationale.yaml`; `scripts/dependency_rationale.py`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`.

## What is sound

The problem is real: the research table states that `langchain_core` is imported by core modules and tests for messages, tools, callbacks, runnables, and `BaseChatModel`, while it currently arrives transitively through `langgraph` and provider packages (`docs/plan-research-dependency-negative-space.md:17-22`). The current core dependency list names multiple LangChain integration packages and `langgraph`, but not `langchain-core` (`pyproject.toml:24-36`), and the rationale registry likewise has no `langchain-core` entry in the core dependency section (`docs/dependency-rationale.yaml:11-64`). The FR's first consumer is concrete: the dependency resolver on the next install when a future transitive pin shifts (`feature-requests/FR-760-declare-langchain-core-dependency.md:7-12`).

The proposed direction aligns with repo doctrine. The local Scripture names `module_structure` as a boundary where import contracts must be declared, not assumed (`.github/copilot-instructions.md:47-63`), and FR-218 established the precedent that documented architecture claims should become mechanical contracts rather than convention (`feature-requests/FR-218-import-linter-architectural-boundary-enforcement.md:17-30`). The dependency-rationale script already provides a repo-native strict check for declared dependencies and stale rationale entries (`scripts/dependency_rationale.py:242-341`), so adding the dependency plus a registry entry is feasible without inventing a new mechanism.

The scope is strategically valid as a framework dependency-contract primitive: the cited evidence covers more than three core uses of the same foreign contract (`docs/plan-research-dependency-negative-space.md:67-80`), and the FR explicitly defers the larger YAMLGraph-native model adapter refactor (`feature-requests/FR-760-declare-langchain-core-dependency.md:46-49`).

**Prior art:** the only hit is FR-760's own body (its sibling counted as a self-match); no other feature request declares `langchain-core` or the honesty-fix pattern. FR-761 and FR-762 are sibling FRs from the same research doc with disjoint scope (lockfile/scanner governance and example taxonomy respectively) and are already cross-referenced in the Related section — not duplicates.

## Required revisions

### R-1: Remove the direct-import scan guard from this FR

Delete or rewrite Proposed Solution step 4 so FR-760 does not authorize a new direct-import scan, governance gate, CI hook, or script behavior change. The current wording says to "extend or verify the direct-import scan" while also saying FR-761 owns the governance gate (`feature-requests/FR-760-declare-langchain-core-dependency.md:30-36`); that is a single-responsibility and scope ambiguity. FR-760 may verify only the existing `scripts/dependency_rationale.py --strict` rationale gate. Any new direct-import enforcement belongs to FR-761.

### R-2: Make the version floor derivation explicit

Replace `>=<current-tested-floor>` with a mechanically foldable rule: after the implementation environment resolves `pip install -e ".[dev]"`, record the resolved `langchain-core` version and use that exact resolved version as the minimum floor in `pyproject.toml`. The current placeholder is directionally sound but underspecified (`feature-requests/FR-760-declare-langchain-core-dependency.md:30-35`).

### R-3: Require a substantive rationale entry, not mere presence

Revise the rationale acceptance criterion to require a `langchain-core` entry with `rationale`, `modules`, and `added` fields. The `modules` list must name representative core import consumers for messages/tools/callbacks/runnables/model types. The existing script requires only `rationale` (`scripts/dependency_rationale.py:20-22`, `scripts/dependency_rationale.py:293-301`), while repo doctrine warns that presence checks without substance are compliance theatre (`.github/copilot-instructions.md:65-115`).

### R-4: Add the doctrine-required reflection criterion

Add a diary reflection acceptance criterion for the implementation PR. Repo doctrine requires reflection after completing a task list (`.github/copilot-instructions.md:31-33`), and the FR currently requires only dependency, rationale, install/test, and changelog artifacts (`feature-requests/FR-760-declare-langchain-core-dependency.md:39-44`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `pyproject.toml` core `[project.dependencies]`: add `langchain-core>=<resolved-version>` |
| D-2 | `docs/dependency-rationale.yaml`: add substantive `langchain-core` entry |
| D-3 | `changelog/unreleased/<fragment>.md`: document the dependency-contract change |
| D-4 | `docs/diary/<date>-<slug>.md`: implementation reflection |
| D-5 | FR implementation notes/status: record resolved version decision and any deviation |

Not authorized: YAMLGraph-native model adapter contracts; provider refactors; LangChain replacement work; lockfile/constraints workflow; `pip-audit` dependency changes; OpenTelemetry extras or tracing work; example dependency taxonomy changes; direct-import scan implementation; CI/pre-commit/hook changes; modifications to judge/review doctrine.

## Revised acceptance criteria

- [ ] AC-01: `pyproject.toml` contains `langchain-core>=<resolved-version>` in core `[project.dependencies]`, where `<resolved-version>` is the exact version resolved in the implementation environment after `pip install -e ".[dev]"`.
- [ ] AC-02: `docs/dependency-rationale.yaml` contains a `langchain-core` entry with non-empty `rationale`, `modules`, and `added` fields; `modules` names representative core import consumers for message, tool, callback, runnable, and chat-model contracts.
- [ ] AC-03: `python scripts/dependency_rationale.py --strict` passes.
- [ ] AC-04: `pip install -e ".[dev]"` resolves without dependency conflict.
- [ ] AC-05: The targeted dependency/rationale checks and the unit suite pass without relaxing existing gates.
- [ ] AC-06: A changelog fragment exists under `changelog/unreleased/` describing FR-760.
- [ ] AC-07: A diary reflection exists under `docs/diary/` for the implementation.
- [ ] AC-08: The FR is updated with implementation status, the resolved `langchain-core` version used as the floor, and any deviations from the judgement.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement or modify direct-import scan governance in this FR; defer that to FR-761. | GATE |
| C-2 | Do not introduce a YAMLGraph-native model adapter, provider abstraction, or LangChain replacement surface. | GATE |
| C-3 | Do not edit CI, hooks, judge doctrine, review doctrine, or other enforcement infrastructure for this dependency declaration. | GATE |
| C-4 | The rationale entry must be substantive; a placeholder that merely satisfies the current script's `rationale` presence check does not satisfy AC-02. | GATE |
| C-5 | If the resolver exposes a conflict between `langchain-core` and existing `langchain-*`/`langgraph` pins, stop and amend the FR instead of widening scope into dependency-governance redesign. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, the enforcer may add `langchain-core` as an explicit core dependency, document its rationale, and verify the existing dependency/install/test gates only.
