# Judgement: FR-954 faithful no-fork import simulation

**Verdict:** APPROVED WITH REVISIONS — the remaining test-fidelity repair is real, minimal, and feasible, but authority activates only after R-1 through R-4 are folded into the FR and this draft is human-reviewed.

**Reviewed against:** `feature-requests/FR-954-fr950-residuals-fork-sim-and-cap198-attribution.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `tests/unit/test_fr713_persistent_bridge.py`; `yamlgraph/utils/bridge.py`; `capabilities/CAP-198-persistent-bridge-loop.yaml`; `ARCHITECTURE.md`; `changelog/unreleased/fr-950-windows-safe-bridge-fork-registration.md`; `tests/unit/test_changelog_req_cross_wiring.py`; `feature-requests/FR-713-persistent-bridge-loop.md`; `feature-requests/FR-952-optional-extras-must-skip-not-error.md`; `feature-requests/FR-953-windows-posix-shell-misattribution.md`; committed merge evidence `82111177`, including `changelog/unreleased/fr-950-cap198-attribution.md` and its diffs for CAP-198, ARCHITECTURE, and the FR-713 witness.

**Prior art:** hook hits dispositioned — FR-944 / FR-944.judgement (map-index attribution: shares only the word "attribution"; different capability, no overlap); FR-951.judgement (UTF-8 boundaries: cites fr950/fork as history, not scope; no overlap); FR-186 (FSM pre-commit gates: "sim" is a substring coincidence; no simulation content). None constrains or duplicates this judgement.

## What is sound

The residual defect is concrete. The current witness pre-imports `asyncio`, `random`, and `langgraph.checkpoint.base`, then removes only `os.register_at_fork` (`tests/unit/test_fr713_persistent_bridge.py:117-130`). That setup proves YAMLGraph's local guard but does not exercise the no-fork capability surface described by REQ-YG-541, where both fork facilities are absent (`capabilities/CAP-198-persistent-bridge-loop.yaml:20-29`; `ARCHITECTURE.md:2531-2535`). Removing both attributes before the ordinary dependency import chain and asserting their absence is a direct, mechanically testable correction.

The proposed implementation is also architecture-aligned and minimal. Production already normalizes the optional OS capability with `getattr(os, "register_at_fork", None)` (`yamlgraph/utils/bridge.py:83-86`), so no production change is needed. The FR rejects vendor patching, mocking, and skipping (`feature-requests/FR-954-fr950-residuals-fork-sim-and-cap198-attribution.md:119-123`), preserving the real import seam and the repo's `mock_escape_hatch` and boundary-normalization doctrine.

Defect B is conclusively complete rather than part of the residual implementation: CAP-198 already attributes both FR-713 and FR-950 (`capabilities/CAP-198-persistent-bridge-loop.yaml:4-5`), the registry parser already supports comma-separated FR ownership (`tests/unit/test_changelog_req_cross_wiring.py:24-38`), and merge `82111177` records the shipped change. Purging that completed concern leaves one responsibility.

Under the rubric this is **Contrib/example**, not a framework primitive: one deterministic platform-capability simulation has a fidelity gap, while the existing production abstraction already fits. Tests can be derived directly once the acceptance criteria below replace the stale aggregate and completed-work criteria.

## Required revisions

### R-1: Make FR-954 identify and authorize only the remaining defect

Rename the H1 to `FR-954: Faithful no-fork import simulation` and rewrite the status, first-consumer statement, Summary, Value Statement, Problem, Proposed Solution, and Related sections so their present-tense scope is only the test witness. The first-consumer statement must describe the current event: clean main is green after `82111177`, but the contributor reads a witness that bypasses the normal dependency import chain and therefore overclaims Windows/no-fork fidelity. Move Defect B and PR #555 to a short implementation-history paragraph.

Delete Proposed Solution B and remove completed AC-03/AC-04 from the active criteria. Do not describe the already-landed CAP attribution as work FR-954 will perform. The current text says the remaining scope is Defect A only (`feature-requests/FR-954-fr950-residuals-fork-sim-and-cap198-attribution.md:18-28`) while the title, first-consumer statement, Problem B, Proposed Solution B, and active checklist still describe two defects (`:1`, `:8`, `:68-78`, `:98-115`); that contradiction prevents scope freeze.

### R-2: Add the missing ideal result

Insert an `## Ideal Result` section before Proposed Solution, as required by the FR template and Scripture (`feature-requests/TEMPLATE.md:59-63`; `.github/copilot-instructions.md:204-206`). Fold in this boundary:

> The import witness exercises the Windows-equivalent OS capability surface -- neither `os.fork` nor `os.register_at_fork` exists -- while importing YAMLGraph through its ordinary cold dependency chain and proving that no bridge loop starts; production behavior and registry attribution remain unchanged.

Use "Windows-equivalent OS capability surface", not a claim that deleting two POSIX attributes simulates every property of Windows.

### R-3: Repair the in-body research record

Make the research record satisfy the prospective FR-890 substance gate (`.github/skills/judge-fr/doctrine.md:118-128`):

1. Restrict it to the remaining Defect A decision.
2. Present four genuine solution classes: the chosen two-attribute capability simulation plus the existing vendor-patch, mock, and skip alternatives.
3. Add a **Strongest dissent** paragraph for the best rejected alternative and resolve it with cited evidence.
4. Add the explicit answer: **`is_this_a_graph`? No. This is one deterministic subprocess witness edit; it has no model stage, multi-stage LLM pipeline, or fan-out.**
5. Remove or correct the claim that every row has an executed probe: the mock alternative currently says `n/a (design inspection)` (`feature-requests/FR-954-fr950-residuals-fork-sim-and-cap198-attribution.md:9,122`).

FR-952 demonstrates the cited in-body route with both preserved dissent and the graph answer (`feature-requests/FR-952-optional-extras-must-skip-not-error.md:122-129`); citing that precedent does not substitute for carrying its required substance.

### R-4: Replace the active acceptance list with the revised criteria below

The current AC-01 checks only a terminal green result, AC-02 checks only `os.fork`, AC-05 separately describes scaffold removal, and AC-03/AC-04 certify work already shipped (`feature-requests/FR-954-fr950-residuals-fork-sim-and-cap198-attribution.md:109-115`). Replace the list verbatim with the revised acceptance criteria below so the setup, path, environment, lifecycle, and prohibited surfaces are all mechanically inspectable.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Correct only `TestImportAndForkSafety.test_import_without_register_at_fork_capability` in `tests/unit/test_fr713_persistent_bridge.py` so its cold subprocess removes and asserts both absent OS capabilities before the ordinary YAMLGraph import chain. |
| D-2 | Fold R-1 through R-4 into `feature-requests/FR-954-fr950-residuals-fork-sim-and-cap198-attribution.md`, then record implementation status and decisions there. |
| D-3 | Add the required FR-954 `type: fix` changelog fragment and one `docs/diary/` reflection with a `Seed:`; allocate no new capability or requirement. |

Not authorized: changes to `yamlgraph/utils/bridge.py`; dependency or constraint changes; vendor patches; mocks or skips; changes to CAP-198, ARCHITECTURE, the FR-950 fragments, or `tests/unit/test_changelog_req_cross_wiring.py`; reopening Defect B; FR-952/FR-953 work; ramp-installer work; broader Windows simulation claims; unrelated refactoring.

## Revised acceptance criteria

- [ ] AC-01: In `test_import_without_register_at_fork_capability`, the subprocess imports only `os` before setup; removes both `fork` and `register_at_fork` when present; asserts `not hasattr(os, "fork")` and `not hasattr(os, "register_at_fork")`; only then imports `yamlgraph`, `yamlgraph.utils.bridge`, and `threading`; and asserts that `yamlgraph-bridge-loop` did not start.
- [ ] AC-02: The subprocess contains no pre-import of `asyncio`, `random`, or `langgraph.checkpoint.base`, so the ordinary cold YAMLGraph dependency chain remains the seam under test.
- [ ] AC-03: On CPython 3.14 in the pinned `[dev]` environment with `uuid_utils >= 0.17.0`, `pytest tests/unit/test_fr713_persistent_bridge.py -q --no-cov` exits zero. The validation record includes a `python` preflight that mechanically reports the Python and `uuid_utils` versions.
- [ ] AC-04: Git history contains separate RED and GREEN commits: RED adds the missing `os.fork`-absence assertion to the current one-attribute setup and records its failure; GREEN removes both attributes, removes the pre-import scaffold, and makes the targeted test file green.
- [ ] AC-05: The implementation diff contains no production, CAP, ARCHITECTURE, dependency, constraint, collision-test, or FR-950-fragment change; the FR records implementation status, a `type: fix` FR-954 changelog fragment exists without a new CAP/REQ allocation, and the final diary entry contains `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into the committed FR before implementation authority is exercised. | GATE |
| C-2 | Obtain human review of this draft judgement; until then it is advisory. | GATE |
| C-3 | Preserve the test-only boundary in the scope table; any production, registry, architecture, dependency, or completed Defect B change requires a new judged scope. | GATE |
| C-4 | Preserve RED-before-GREEN as separate commits and retain the failing output in the FR implementation record. | GATE |
| C-5 | Validate on the specified CPython 3.14 pinned environment; a green run on another interpreter does not satisfy AC-03. | GATE |

Authority granted: after C-1 and C-2 are satisfied, the enforcer may correct the single FR-713 subprocess witness and add only the FR-954 lifecycle artifacts listed above.
