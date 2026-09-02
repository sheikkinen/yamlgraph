# Judgement: FR-950 Windows-safe bridge fork registration

**Outcome (2026-09-02, post-hoc):** revisions R-1–R-5 were folded into the committed artifacts (`086edaf2`), but gate C-1 was **waived by the operator, not cleared** — no rejudgement was ever rendered. The sole judge route (`scripts/judge.sh` → `yamlgraph graph run`) imports `yamlgraph`, which is the very call this FR repairs, and the host's WSL install was broken, so no POSIX fallback existed. Enforcement proceeded under that explicit waiver: RED `f8556dcb`, GREEN `547bd58a`, registry alignment `f5c60d73`. The verdict below is the original and remains unamended; it did not authorize this work. AC-07 was **not** met and is dispositioned in the FR's Implementation Status. A rejudgement from a fork-capable host is still owed.

**Verdict:** REJECTED — the callsite correction is minimal and technically sound, but the committed research record does not satisfy the prospective research-substance gate; no implementation authority exists until the revisions below are folded into the FR and independently rejudged.

**Reviewed against:** `feature-requests/FR-950-windows-safe-bridge-fork-registration.md`; `feature-requests/FR-950.research.md`; `feature-requests/research-briefs/fr-950-windows-bridge-import-brief.md`; `feature-requests/FR-713-persistent-bridge-loop.md`; `feature-requests/FR-949-issue-queue-delegation.md`; `feature-requests/FR-709-race-loser-teardown-integration.md`; `feature-requests/FR-299-promptfoo-router-eval-demo.md`; `feature-requests/FR-346-extract-shared-fsm-bridge-phase1.md`; `feature-requests/FR-369-fsm-snapshot-hooks-phase2-subclassing.md`; `yamlgraph/utils/bridge.py`; `tests/unit/test_fr713_persistent_bridge.py`; `ARCHITECTURE.md`; `pyproject.toml`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

| Criterion | Assessment |
|---|---|
| Scope | Sound and minimal. The FR limits the production change to capability-guarding the single unconditional registration at `yamlgraph/utils/bridge.py:83`, explicitly excluding platform-name branching, shims, dependencies, and new abstractions (`feature-requests/FR-950-windows-safe-bridge-fork-registration.md:67-84`). |
| Consistency | The problem, ideal result, solution, and main criteria agree that no-fork runtimes skip registration while fork-capable runtimes preserve child reset (`feature-requests/FR-950-windows-safe-bridge-fork-registration.md:32-35,50-63,67-81,88-91`). R-2 and R-3 below remove residual witness and verification ambiguity. |
| Measurability | AC-01 through AC-04 and AC-08 identify observable imports, thread state, fork behavior, prohibited implementation shapes, and traceability (`feature-requests/FR-950-windows-safe-bridge-fork-registration.md:88-95`). AC-07 and AC-09 are not yet mechanically exact and require R-3. |
| Feasibility | The target is a module-level call with no dependent state (`yamlgraph/utils/bridge.py:66-83`), Python 3.13 is inside the declared range (`pyproject.toml:10`), and the committed research records convergent support for runtime capability detection (`feature-requests/FR-950.research.md:15-19`). |
| Architecture alignment | The change normalizes at the external platform boundary, matching repository doctrine (`.github/copilot-instructions.md:41-43`), and preserves FR-713's child-reset requirement (`feature-requests/FR-713-persistent-bridge-loop.md:256-261`). The requirement text itself must be made capability-accurate under R-4 because it currently states the registration behavior without a runtime qualifier (`ARCHITECTURE.md:2534`). |
| Single responsibility | One defect is addressed: optional fork-hook registration during bridge import. The cited issue-queue, live teardown, Promptfoo, and FSM bridge precedents concern distinct surfaces, as their own summaries show (`feature-requests/FR-949-issue-queue-delegation.md:21-23`; `feature-requests/FR-709-race-loser-teardown-integration.md:40-42`; `feature-requests/FR-299-promptfoo-router-eval-demo.md:10-12`; `feature-requests/FR-346-extract-shared-fsm-bridge-phase1.md:9-15`; `feature-requests/FR-369-fsm-snapshot-hooks-phase2-subclassing.md:9-19`). No split is warranted. |
| Strategic classification | **Framework primitive correction.** CAP-198/REQ-YG-541 owns a shared bridge substrate used by race and router-race compilation (`ARCHITECTURE.md:516,2534`), and the defect blocks package import, CLI entry, and test collection (`feature-requests/FR-950-windows-safe-bridge-fork-registration.md:37-48`). This is not a contrib example or documentation-only pattern. |
| Testability | Direct RED witnesses are derivable for missing capability, import side effects, and retained POSIX reset. Existing tests already provide fresh-subprocess lazy-import and real-fork-after-warmup seams (`tests/unit/test_fr713_persistent_bridge.py:104-136`). R-2 must pin the absent-capability setup so failure reflects missing implementation rather than import order. |

The strongest case against the proposal is not the two-line fix; it is that the evidence gate could be satisfied cosmetically by repeating the preferred answer. That failure is present here: four rows restate the same conditional-registration solution, while only the subtractionist row materially differs (`feature-requests/FR-950.research.md:15-19`). The judge doctrine requires 4-6 genuine solution classes, precedent lines, preserved disagreement, and an `is_this_a_graph` answer, and explicitly withholds authority from a shape-only record (`.github/skills/judge-fr/doctrine.md:118-129`).

## Required revisions

### R-1: Replace persona repetition with substantive alternatives research

Rewrite `feature-requests/FR-950.research.md` so it compares 4-6 genuinely distinct solution classes rather than counting four formulations of the same capability guard as four alternatives. At minimum, independently assess: guarded import-time registration; an isolated helper owning optional hook registration; lazy one-time registration before first bridge use; decoupling bridge import from package/CLI initialization; and removal of child reset. For each class, state the governing precedent, concrete benefit, concrete failure mode, disposition, and `is_this_a_graph` answer. Preserve the subtractionist disagreement instead of folding it into a false convergence.

Remove CAP-141 and CAP-209 as claimed precedents unless the revised record demonstrates a concrete contract they govern. CAP-141 is the FSM bridge and CAP-209 is root package seams, while the registered persistent-loop owner is CAP-198/REQ-YG-541 (`ARCHITECTURE.md:461,516,527`). Cite FR-713 directly as the controlling behavioral precedent.

### R-2: Specify the absent-capability RED witness completely

Amend the test plan and AC-01/AC-02 to require a fresh subprocess that, before the first `yamlgraph` import:

1. imports `os` and `threading`;
2. deletes `os.register_at_fork` only when present;
3. imports both `yamlgraph` and `yamlgraph.utils.bridge`;
4. asserts no thread named `yamlgraph-bridge-loop` exists; and
5. exits nonzero with captured stderr on any failure.

State that this subprocess-local deletion is test setup, does not add or replace an `os` attribute, and cannot mutate the parent process. Keep the existing real-fork witness as the behavioral proof for the present-capability path (`tests/unit/test_fr713_persistent_bridge.py:116-136`).

### R-3: Make Windows and completion criteria executable

Replace AC-07 with the exact Windows command already recorded by the evidence:

`.venv/Scripts/python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto`

Require exit code zero and successful collection, not merely that the suite "reaches collection" (`feature-requests/research-briefs/fr-950-windows-bridge-import-brief.md:74-78`).

Replace AC-09 with named artifact assertions: one `type: fix` changelog fragment under `changelog/unreleased/`; an `Implementation Status` section in FR-950 containing dated command/result records for AC-05 through AC-08; and one new `docs/diary/` entry containing a named trap or insight, an extracted heuristic, and a `Seed:` line. Do not make diary or status prose a substitute for the executable witnesses.

### R-4: Qualify the existing requirement instead of leaving a false universal claim

Add `ARCHITECTURE.md` to the deliverables and revise REQ-YG-541 in place so it requires `_reset_after_fork` registration only when the runtime exposes `os.register_at_fork`, requires no fork setup when absent, and preserves lazy import on both paths. Keep the same REQ and CAP allocation. The current unqualified wording would become false on the newly supported Windows path (`ARCHITECTURE.md:2534`).

### R-5: Record the mandatory RED-GREEN enforcement sequence

Add an enforcement condition requiring the absent-capability witness to be committed RED before the production guard, then committed GREEN after the smallest production change. Repository doctrine requires a failing witness before a bug fix and separate RED/GREEN proof (`.github/copilot-instructions.md:194`).

## Scope is frozen

Because the verdict is REJECTED, implementation scope is frozen at zero. Only planning-artifact repair is authorized before rejudgement.

| Deliverable | Surface |
|---|---|
| D-1 | Revise `feature-requests/FR-950.research.md` per R-1. |
| D-2 | Revise `feature-requests/FR-950-windows-safe-bridge-fork-registration.md` per R-2 through R-5. |
| D-3 | Submit the revised committed artifacts for a new independent judgement. |

Not authorized: edits to `yamlgraph/utils/bridge.py`; edits to tests; edits to `ARCHITECTURE.md`; platform-name branches; exception-swallowing registration; fake or replacement `os` APIs; fallback callbacks; bridge lifecycle refactors; package import-graph refactors; changes to fork-reset contents; new dependencies, CAPs, REQs, graphs, prompts, CLI wrappers, or CI infrastructure.

## Revised acceptance criteria

The following criteria are the mechanically foldable target for a resubmitted FR; they do not grant implementation authority.

- [ ] AC-01: A fresh subprocess deletes `os.register_at_fork` when present before any `yamlgraph` import, then imports `yamlgraph` and `yamlgraph.utils.bridge` successfully.
- [ ] AC-02: The AC-01 subprocess asserts that no `yamlgraph-bridge-loop` thread exists after both imports and reports captured stderr on failure.
- [ ] AC-03: On a runtime exposing `os.register_at_fork`, the real fork-after-warmup witness proves that a child receives fresh lazy loop and client-cache state.
- [ ] AC-04: Production code detects the capability at the `yamlgraph/utils/bridge.py` callsite; it does not branch on platform-name strings, catch registration exceptions, or add, replace, or delete attributes on `os`.
- [ ] AC-05: `.venv/Scripts/yamlgraph.exe graph lint examples/demos/hello/graph.yaml` exits zero on Windows without an invocation workaround.
- [ ] AC-06: `.venv/Scripts/python.exe -m pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov` exits zero on Windows, with only the real-fork witness skipped for lack of `os.fork`.
- [ ] AC-07: `.venv/Scripts/python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto` exits zero on Windows and completes collection.
- [ ] AC-08: Every new test carries `@pytest.mark.req("REQ-YG-541")`, and `python scripts/req_coverage.py --strict` exits zero.
- [ ] AC-09: REQ-YG-541 states the present-capability registration behavior and absent-capability no-op behavior under the existing CAP-198 allocation.
- [ ] AC-10: The absent-capability witness is committed RED before the production edit and GREEN afterward in a separate commit.
- [ ] AC-11: A `type: fix` changelog fragment names FR-950 and REQ-YG-541.
- [ ] AC-12: FR-950 records dated commands and results for AC-05 through AC-08, and a diary entry records a trap or insight, heuristic, and `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-5 are folded into committed FR/research artifacts and a new independent judgement grants authority. | GATE |
| C-2 | The RED commit changes only the witness; the GREEN commit makes the smallest sufficient callsite and requirement-text changes. | GATE |
| C-3 | The present-capability path retains FR-713's real child-reset behavior; a skipped or mocked fork witness is not proof of that path. | GATE |
| C-4 | The absent-capability witness mutates only its disposable subprocess and never installs a fake `os.register_at_fork`. | GATE |
| C-5 | No adjacent bridge lifecycle, cache, package-import, CLI, dependency, graph, prompt, CAP, REQ-allocation, or CI change enters enforcement. | GATE |

Authority granted: none; only the committed planning revisions D-1 through D-3 may proceed before rejudgement.
