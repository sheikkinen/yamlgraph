# Judgement: FR-799 Repair fr432 Fixture sys.modules Orphaning of yamlgraph.config

**Verdict:** APPROVED WITH REVISIONS - the defect and one-fixture cure are proven and minimal, but authority activates only after the FR makes the permanent regression witness and process-gate artifacts explicit.

**Prior art:** dispositioned in the parent FR's Prior art line (FR-798 owns the investigation and disposition; FR-432 owns the fixture; FR-756 confirms no marker/lane change) and re-verified against the cited artifacts in the Reviewed-against record below — no undispositioned overlap found.

**Reviewed against:** `feature-requests/FR-799-fr432-fixture-sys-modules-orphan.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; cited prior art `feature-requests/FR-798-full-suite-failure-classification-investigation.md`, `feature-requests/FR-798-full-suite-failure-classification-investigation.judgement.md`, `feature-requests/FR-432-dotenv-upward-search.md`, `feature-requests/FR-756-core-test-isolation.md`; cited evidence `docs/investigations/fr798-full-suite-failures.md`, `docs/diary/diary-2026-08-15-fr798-failure-classification.md`, `tests/unit/test_fr432_dotenv_upward_search.py`, `tests/unit/test_runpod_provider.py`, `logs/fr798-classA-witness2.log`, `logs/fr798-classA-xdist20.log`, `logs/fr798-py312-classA.log`, `logs/fr798-classA-serial10.log`.

## What is sound

The problem is real and already narrowed to one test-isolation boundary. FR-799 states that `_restore_config_module_state` pops `yamlgraph.config` without re-importing, leaving the `yamlgraph` package attribute pointed at an orphaned module and causing a later `from yamlgraph import config` plus `importlib.reload(config)` to raise (`feature-requests/FR-799-fr432-fixture-sys-modules-orphan.md:14-20`). The current fr432 fixture matches that claim exactly: teardown performs `sys.modules.pop("yamlgraph.config", None)` and then only clears env/chdir state (`tests/unit/test_fr432_dotenv_upward_search.py:16-22`). The victim fixture and test in RunPod reload the package-level `config` object (`tests/unit/test_runpod_provider.py:25-33`, `tests/unit/test_runpod_provider.py:117-133`).

The cited investigation proves the causal chain rather than guessing from a flaky red. FR-798 records the same four-step mechanism, including the parent package attribute returning the orphan before `importlib.reload` checks `sys.modules` identity (`docs/investigations/fr798-full-suite-failures.md:45-57`). The evidence includes 10/10 serial passes, 1/20 xdist reproduction, and a deterministic two-module witness on both Python 3.14.6 and 3.12.11 (`docs/investigations/fr798-full-suite-failures.md:23-43`; `logs/fr798-classA-serial10.log:1-10`; `logs/fr798-classA-xdist20.log:20-23`; `logs/fr798-classA-witness2.log:1-87`; `logs/fr798-py312-classA.log:1-88`). The diary independently names the same trap as `attribute_orphan_after_pop` (`docs/diary/diary-2026-08-15-fr798-failure-classification.md:19-29`).

The proposed cure is the smallest correct boundary fix: repair the polluting fr432 teardown, not the RunPod victim fixture. That aligns with FR-798's disposition that Class A is a one-line test correction in fr432, not a runtime or retry/serialization change (`docs/investigations/fr798-full-suite-failures.md:68-77`). It also follows repo doctrine: own red test pollution rather than calling it external noise (`.github/copilot-instructions.md:25-28`), write the failing witness before fixing (`.github/copilot-instructions.md:220-221`), and normalize at the boundary where the bad state is introduced (`.github/copilot-instructions.md:49-52`, `.github/copilot-instructions.md:246-249`). Strategic classification: **pattern documentation / test correction**, not a framework primitive; no production abstraction is warranted.

## Required revisions

### R-1: Specify the durable RED/GREEN witness artifact

Amend the Proposed Solution and AC-01 so the enforcer knows exactly what must be committed or recorded as the permanent regression witness. The current text says "mechanize the FR-798 2-module witness as a permanent regression test" and then gives a one-off command (`feature-requests/FR-799-fr432-fixture-sys-modules-orphan.md:65-72`), while AC-01 requires "A committed regression witness" (`feature-requests/FR-799-fr432-fixture-sys-modules-orphan.md:79-81`). Fold in this binding wording:

> The RED/GREEN witness is the two-module pytest command already cited. Enforcement must run it before the fix and record the RED output in the implementation notes or commit trail, then run the identical command after the fix and record GREEN. If a new test or helper is added to make the witness permanent, it must live under `tests/unit/`, carry `@pytest.mark.req("REQ-YG-043")` or another valid existing requirement ID, and must not invoke nested pytest from the default suite.

This keeps the TDD witness mandatory without authorizing a slow or fragile test harness.

### R-2: Add the required process-gate artifacts

Add acceptance criteria for the process artifacts required by repo doctrine and CI gates: a changelog fragment under `changelog/unreleased/`, a diary entry under `docs/diary/`, and a completion note in the FR. Repo doctrine says all code edits live under a judged FR and the FR is the source of implementation status (`.github/copilot-instructions.md:33-35`, `.github/copilot-instructions.md:233-236`); branch protection gates `feat`/`fix` PRs on changelog and diary artifacts (`.github/copilot-instructions.md:228-236`). These artifacts are not product scope expansion; they are enforcement evidence for this bug fix.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/unit/test_fr432_dotenv_upward_search.py` fixture teardown restoration |
| D-2 | RED/GREEN evidence for the two-module witness command: `pytest tests/unit/test_fr432_dotenv_upward_search.py "tests/unit/test_runpod_provider.py::TestRunpodProvider::test_default_model_reads_env_without_fallback" -q --no-cov -p no:randomly` |
| D-3 | Optional unit-level regression assertion/helper under `tests/unit/` only if it is fast, non-nested, and requirement-marked |
| D-4 | `feature-requests/FR-799-fr432-fixture-sys-modules-orphan.md` updated with judgement, implementation status, witness outcome, and deviations if any |
| D-5 | Changelog fragment under `changelog/unreleased/` and diary reflection under `docs/diary/` |

Not authorized: production changes under `yamlgraph/**`; changes to `tests/unit/test_runpod_provider.py` except incidental import-format fallout from tooling; retries, sleeps, suite serialization, test deselection, marker/lane changes, CI/hook edits, dependency changes, graph or prompt artifact edits, or a conftest-wide orphan detector. The diary Seed in FR-798 about a conftest orphan detector is explicitly separate follow-up scope (`docs/diary/diary-2026-08-15-fr798-failure-classification.md:68-74`).

## Revised acceptance criteria

- [ ] AC-01: FR-799 is amended with R-1 and R-2 before enforcement authority is used.
- [ ] AC-02: The two-module witness command from D-2 is run before the fix and fails with `ImportError: module yamlgraph.config not in sys.modules`, matching the cited FR-798 witness.
- [ ] AC-03: The fr432 fixture teardown restores `sys.modules["yamlgraph.config"]` and the `yamlgraph.config` package attribute to the same live module object after every fr432 test.
- [ ] AC-04: The same two-module witness command from D-2 passes after the fixture fix.
- [ ] AC-05: All tests in `tests/unit/test_fr432_dotenv_upward_search.py` pass with their fresh-import semantics preserved.
- [ ] AC-06: The targeted RunPod reload test still passes when run after the fr432 module in one process.
- [ ] AC-07: The fast unit suite passes serially and under `-n auto`.
- [ ] AC-08: No retries, sleeps, serialization, test deselection, marker/lane changes, production changes, graph/prompt edits, CI/hook edits, or dependency changes are made.
- [ ] AC-09: A changelog fragment, diary entry, and FR-799 completion note are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 and R-2 are folded into `feature-requests/FR-799-fr432-fixture-sys-modules-orphan.md`. | GATE |
| C-2 | Fix the polluter (`tests/unit/test_fr432_dotenv_upward_search.py`), not the RunPod victim fixture, unless the exact RED/GREEN witness proves that the proposed teardown repair is insufficient. | GATE |
| C-3 | Preserve FR-432 semantics: config import must still re-run dotenv loading from the current working directory for each fr432 case. | GATE |
| C-4 | If the implementation needs production code, CI/hook policy, marker/lane changes, dependency changes, or a conftest-wide orphan detector, stop and return with a separate judged FR. | GATE |

Authority granted: after the required revisions are folded, enforcement may repair the fr432 autouse fixture teardown and add only the minimal unit-test/process evidence needed to prove the module-identity orphan is gone.
