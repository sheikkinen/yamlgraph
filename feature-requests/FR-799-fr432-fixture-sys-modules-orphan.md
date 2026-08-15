# Feature Request: Repair fr432 Fixture sys.modules Orphaning of yamlgraph.config

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (revisions folded below; see `FR-799-fr432-fixture-sys-modules-orphan.judgement.md`)
**Effort:** 0.5 hours
**Requested:** 2026-08-15
**First consumer / first event:** the next enforcer whose pre-commit pytest hook (xdist, `-n auto`) schedules `test_fr432_dotenv_upward_search.py` on the same worker as `test_runpod_provider.py` without an intervening `yamlgraph.config` import — the first event is a red `ImportError: module yamlgraph.config not in sys.modules` blocking an unrelated commit (~5% per full-suite run, measured 1/20 in FR-798).

**Prior art:** FR-798 (Class A investigation — owns the causal chain, deterministic witness, and this disposition: "test correction (fixture re-import)"), FR-432 (the dotenv upward-search tests whose fixture is the defect), FR-756 (test classification precedent — no marker or lane changes here).

## Summary

The autouse fixture `_restore_config_module_state` in
`tests/unit/test_fr432_dotenv_upward_search.py:20` pops `yamlgraph.config`
from `sys.modules` without re-importing, orphaning the `config` attribute
still held by the `yamlgraph` package object. Any later
`from yamlgraph import config` + `importlib.reload(config)` in the same
process raises `ImportError` unless an intervening import heals the orphan.
Restore module identity in the fixture teardown.

## Value Statement

Enforcers stop losing commits to a scheduling-lottery red in the mandatory
pre-commit gate; the only nondeterministic failure in the default unit lane
is eliminated at its root.

## Problem

Proven causal chain (FR-798 report, `docs/investigations/fr798-full-suite-failures.md`):

1. fr432 teardown: `sys.modules.pop("yamlgraph.config", None)` — no re-import.
2. `yamlgraph` package attribute `config` still references the orphaned module.
3. runpod's `restore_config` fixture: `from yamlgraph import config` returns
   the orphan (attribute lookup precedes submodule import).
4. `importlib.reload(config)` → `sys.modules.get(name) is not module` →
   `ImportError`.

Serial runs are healed by sibling tests re-importing `yamlgraph.config`;
xdist reproduces at ~5%/run (1/20 full-suite runs; deterministic 2-module
witness reproduces at 100%, identically on Python 3.14.6 and 3.12.11).

## Ideal Result

Every test that pops or reloads `yamlgraph.config` leaves `sys.modules` and
the `yamlgraph` package attribute pointing at the same live module object,
so test order and worker scheduling cannot affect any other test; the
FR-798 witness command passes deterministically.

## Proposed Solution

In `tests/unit/test_fr432_dotenv_upward_search.py`, make the teardown
restore identity instead of orphaning:

```python
@pytest.fixture(autouse=True)
def _restore_config_module_state() -> None:
    yield
    sys.modules.pop("yamlgraph.config", None)
    importlib.import_module("yamlgraph.config")  # re-register; heals the package attribute
    os.environ.pop(_ENV_KEY, None)
    os.chdir(_ORIGINAL_CWD)
```

RED first: mechanize the FR-798 2-module witness as a permanent regression
test (it fails today):

```bash
pytest tests/unit/test_fr432_dotenv_upward_search.py \
  "tests/unit/test_runpod_provider.py::TestRunpodProvider::test_default_model_reads_env_without_fallback" \
  -q --no-cov -p no:randomly
```

**Witness contract (judgement R-1, binding):** The RED/GREEN witness is the
two-module pytest command above. Enforcement must run it before the fix and
record the RED output in the implementation notes or commit trail, then run
the identical command after the fix and record GREEN. If a new test or
helper is added to make the witness permanent, it must live under
`tests/unit/`, carry `@pytest.mark.req("REQ-YG-043")` or another valid
existing requirement ID, and must not invoke nested pytest from the default
suite.

No retries, no suite serialization, no marker changes (per FR-798 AC-04
boundary). No production files change.

## Acceptance Criteria

(Revised per judgement — supersedes the proposed set.)

- [ ] AC-01: FR-799 is amended with R-1 and R-2 before enforcement authority
  is used.
- [ ] AC-02: The two-module witness command is run before the fix and fails
  with `ImportError: module yamlgraph.config not in sys.modules`, matching
  the cited FR-798 witness.
- [ ] AC-03: The fr432 fixture teardown restores `sys.modules["yamlgraph.config"]`
  and the `yamlgraph.config` package attribute to the same live module
  object after every fr432 test.
- [ ] AC-04: The same two-module witness command passes after the fixture fix.
- [ ] AC-05: All tests in `tests/unit/test_fr432_dotenv_upward_search.py` pass
  with their fresh-import semantics preserved.
- [ ] AC-06: The targeted RunPod reload test still passes when run after the
  fr432 module in one process.
- [ ] AC-07: The fast unit suite passes serially and under `-n auto`.
- [ ] AC-08: No retries, sleeps, serialization, test deselection, marker/lane
  changes, production changes, graph/prompt edits, CI/hook edits, or
  dependency changes are made.
- [ ] AC-09: A changelog fragment, diary entry, and FR-799 completion note
  are included (judgement R-2).

## Alternatives Considered

- **Reload instead of pop in fr432's `_import_config_fresh`:** changes the
  tested semantics (fresh import vs reload differ for module-level dotenv);
  larger blast radius for the same cure.
- **Harden the runpod `restore_config` fixture instead:** fixes the victim,
  not the polluter; any future reload-based test would re-hit the orphan.
  Violates normalize-at-the-boundary (the boundary is where the pop happens).
- **Conftest-wide orphan detector (FR-798 diary Seed):** valuable but a
  separate, larger scope — detection infrastructure vs this one-line defect.

## Related

- `docs/investigations/fr798-full-suite-failures.md` (Class A)
- `docs/diary/diary-2026-08-15-fr798-failure-classification.md`
  (`attribute_orphan_after_pop`)
- `logs/fr798-classA-witness2.log`, `logs/fr798-classA-xdist20.log`
