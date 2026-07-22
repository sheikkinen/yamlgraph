# Feature Request: FR-756 Independently Verifiable Core Test Suite

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced (2026-07-21)
**Effort:** 1–2 days
**Requested:** 2026-07-21
**First consumer / first event:** any agent or CI job that must answer "is the shipped package green?" in isolation; first event is the next core-only change where the author wants proof that failures (or passes) belong to the package and not to examples/chaplain fixtures.

## Summary

The unit test suite (106k lines) mixes tests of the shipped package with tests of repository process artifacts: 51 unit-test files reference `.chaplain`, 43 reference `examples/`, and 31 reference `scripts/` (rg audit, 2026-07-21). There is no command that runs *only* the tests exercising the wheel's contents. "Core is green" is currently not independently verifiable — the monorepo-split review found this is 90% of the benefit a repo split would buy, at ~0% of its cost.

## Value Statement

One command proves the distributed package green without touching `examples/`, `.chaplain/`, or `scripts/`, giving core changes a clean pass/fail signal and making test pollution across the package/process boundary visible as a classification error instead of a mystery.

## Problem

1. **Unverifiable claim:** the wheel excludes `examples*`, `scripts*`, and process trees, but the test suite that gates CI does not mirror that boundary. A green run conflates "package works" with "process tooling works" and "examples work".
2. **Blame ambiguity:** when a run goes red, the author must first determine whether the failure is in package code or in fixtures reaching into `.chaplain/`/`examples/` — the exact test-pollution shape the "pre-existing failure" prohibition exists to fight.
3. **Boundary drift is invisible:** nothing today flags a new core test that quietly grows a dependency on `examples/` fixtures (the `id_registry` leak of FR-754 had exactly this test-shadow: core-located tests reading `.chaplain/`).

## Ideal Result

`pytest tests/unit -m "not process" -q --no-cov` runs the complete set of tests for shipped-package behavior and passes with zero filesystem reads outside the package and test fixtures. CI runs this as a distinct `core-test` job whose name makes the narrower claim explicit. A test that belongs to the core set but references `examples/`, `.chaplain/`, or `scripts/` fails collection, not review.

## Proposed Solution

Marker-based classification with mechanical enforcement — no test-file moves in this FR (moving 106k lines is a separate, optional follow-up). FR-754 must land first, or be enforced first in the same session, so ID-registry tests are not merely classified around an unresolved package leak.

1. **Classify:** add a `process` pytest marker; the unmarked default is core. Mechanically seed the classification from the existing grep inventory (files referencing `examples/`, `.chaplain/`, `scripts/` get `pytestmark = pytest.mark.process` at module level). ~93 files, scriptable.
2. **Enforce the boundary:** extend `tests/conftest.py` collection logic, or an equivalent pytest collection hook, to source-scan each unit test module and fail any *unmarked* module whose source references `examples/`, `.chaplain/`, or `scripts/` — substance check, not presence check (`gate_checks_shape_not_substance`). Keep the first implementation to source-text scanning with a short documented allowlist only for unavoidable false positives; no import tracing or coverage inference.
3. **Preserve normal collection:** the core command may use `--no-cov`, but it must still run through normal `tests/conftest.py` and continue enforcing `@pytest.mark.req`.
4. **CI:** add a `core-test` job running `pytest tests/unit -m "not process" -q --no-cov`; existing full-suite `test` job unchanged.
5. **Document:** testing section in `CLAUDE.md` gains the one-line command.

Boundary cases resolved at Judge time:
- FSM bridge tests: FR-755 ruled position C (contrib tier, 2026-07-21) — contrib ships in the wheel, but FSM test fixtures reach into `.chaplain/`, so they classify as `process` until fixtures are self-contained.
- Tests referencing `examples/` only as YAML fixture data (not example app code): copy the smallest YAML fixture into `tests/fixtures/` when that keeps an otherwise-core test in the core set; broad fixture rewrites are out of scope.

## Acceptance Criteria

- [x] RED: failing test asserting the boundary-lint exists and flags a synthetic unmarked test referencing `.chaplain/` (commit separately, `SKIP=pytest`)
- [x] `pytest tests/unit -m "not process" -q --no-cov` passes and collects > 0 tests
- [x] All test modules referencing `examples/`, `.chaplain/`, or `scripts/` carry the `process` marker (enforced mechanically, not by review)
- [x] Boundary lint/source scan runs during pytest collection; an unmarked unit test module with a process reference blocks collection
- [x] Boundary scanner has only a short documented allowlist for unavoidable false positives; no import-tracing or coverage-inference classifier added
- [x] `core-test` CI job added to `.github/workflows/`
- [x] Marker registered in `pyproject.toml` pytest config (no `PytestUnknownMarkWarning`)
- [x] `CLAUDE.md` testing commands updated
- [x] FR-754 relocation is completed first, or completed earlier in the same enforcement session before ID-registry test classification
- [x] Changelog fragment in `changelog/unreleased/`
- [x] Diary entry

## Judgement (2026-07-21)

**Verdict: AUTHORITY GRANTED WITH CONDITIONS.** The problem is real and the marker-based approach is the minimal viable correction, but enforcement must be precise enough that this does not become a one-time bulk marking ritual.

Raw observation before judgement:

```text
rg -l '\.chaplain' tests/unit | wc -l  -> 51
rg -l 'examples/' tests/unit | wc -l   -> 43
rg -l 'scripts/' tests/unit | wc -l    -> 31
```

`pyproject.toml` currently registers `req`, `integration`, and `slow` only; `tests/conftest.py` already has a `pytest_collection_modifyitems` hook for requirement traceability and is the natural enforcement point for a source-text boundary check.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | The FR says unmarked default is core. That is correct, but it makes collection-time enforcement mandatory; otherwise new boundary leaks will enter silently. | Extend `tests/conftest.py` collection logic or an equivalent pytest collection hook to inspect each unit test module's source text and fail unmarked modules that reference `.chaplain`, `examples/`, or `scripts/`. |
| F2 | A simple substring scan can false-positive on ordinary prose, but that is acceptable for the first gate because the boundary claim is about test source dependency and fixture coupling, not imports alone. | Freeze the first implementation to source-text scanning with a short allowlist only for documented exceptions. Do not build import tracing or coverage inference in this FR. |
| F3 | `scripts/` is both a process boundary and a legitimate target for process tests. Marking those tests as `process` is right; moving them is out of scope. | Add `process` to pytest markers and mechanically add `pytestmark = pytest.mark.process` to existing unit modules that reference `.chaplain`, `examples/`, or `scripts/`, unless the reference is removed by copying a core fixture into `tests/fixtures/`. |
| F4 | `pytest tests/unit -m "not process" -q --no-cov` must not silently bypass the existing requirement marker gate or coverage policy in surprising ways. | The core-test command may use `--no-cov`, but it must still collect through normal `tests/conftest.py` and enforce `@pytest.mark.req`. CI job name must make the narrower claim explicit. |
| F5 | FR-754 should land before or inside this work; otherwise the new classifier will mark ID-registry tests process while the package leak still exists. | Sequence FR-754 first. If combined in one enforcement session, perform FR-754 relocation before adding process markers for ID-registry tests. |
| F6 | FSM bridge classification depends on FR-755's contrib ruling. Contrib ships in the wheel, but current FSM tests are not automatically core if they depend on chaplain fixtures. | Mark current FSM tests process when they read `.chaplain`; a follow-up may make self-contained contrib tests that remain in the core command. |

**Purge list:** no directory migration, no repo split, no coverage/import-tracing classifier, no broad fixture rewrites beyond copying the smallest YAML fixture needed to keep an otherwise-core test in the core set.

**Scope frozen:** marker classification, source-text boundary enforcement, a distinct CI core-test job, and docs for the exact command.

## Alternatives Considered

- **Directory split (`tests/unit/core/` vs `tests/unit/process/`):** cleaner long-term but moves ~100 files in one commit, destroying blame history and colliding with in-flight sessions (`one_session_one_repo`). Markers achieve the verifiability now; a directory migration can follow as mechanical cleanup once the classification is proven stable.
- **Repo split:** rejected by the 2026-07-21 critical review — no named first consumer; this FR delivers the verifiability benefit without the cost.
- **Coverage-based inference (run core-only by measuring imports):** clever, slow, and implicit; classification should be declared and enforced, not inferred per run.

## Related

- Monorepo-split critical review (2026-07-21)
- FR-754 (removes one core/process entanglement this FR would otherwise classify)
- FR-755 (FSM ownership ruling determines FSM test classification)
- Scripture: `gate_checks_shape_not_substance`, `detection_without_enforcement`, "pre-existing failure" prohibition
