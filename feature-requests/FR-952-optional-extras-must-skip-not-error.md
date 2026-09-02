# Feature Request: Absent optional extras must skip the suite, not error it

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-02
**First consumer / first event:** a contributor who ran `pip install -e ".[dev]"` — the documented minimum — runs `pytest tests/unit/ -m "not slow"` for the first time and reads a result they can act on, instead of 18 failures naming third-party modules they were never told to install.
**Research:** in-body dispositioned alternatives table below (FR-889 style; the FR-890 route `scripts/research.sh` is a bash script and this host has no working POSIX shell — see FR-953, which is exactly why that route could not be run here).
**Prior art:**
- [FR-225-a2a-test-coverage.md](FR-225-a2a-test-coverage.md) — the pattern this FR generalizes. It established module-level `pytest.importorskip("a2a")` for an optional extra and confirmed it works. It fixed one extra by hand; this FR asks why nothing prevents the next one from regressing.
- [FR-759 / `core-test`](../.github/workflows/workflow.yml) — the CI job that deliberately omits the `otel` extra "to prove the disabled/missing-extra OTEL tests collect and pass (rather than skip) when opentelemetry-sdk is absent". That is the doctrine this FR extends: it is enforced for exactly one extra, by one job, and for no other.
- [FR-219-dependency-rationale-audit.md](FR-219-dependency-rationale-audit.md) — documents *why* each optional group exists. It says nothing about test behaviour when a group is absent. No overlap.
- [FR-951-declare-utf8-at-text-boundaries.md](FR-951-declare-utf8-at-text-boundaries.md) — the parent. Its Out of Scope names this class explicitly ("19 `ModuleNotFoundError` … reflect an incomplete local venv, not a code defect") and defers it here. This FR disputes half of that: the missing packages are indeed an environment fact, but a *hard error* rather than a skip is a test-suite defect.
- Retrieval is filename-noun IDF ranked and found `importorskip` only where the word appears. The absence of a governing FR is a floor, not proof.

## Summary

A test that cannot run without an optional extra must skip with a named
reason. Today 18 such tests raise `ModuleNotFoundError`, one of them at
collection time, so the suite reports defects that are really absent packages.

## Value Statement

A contributor with the documented `[dev]` install gets a green suite plus an
explicit list of what they skipped, instead of a red suite that hides real
failures behind missing third-party packages.

## Problem

`pytest tests/unit/ -q --no-cov -m "not slow" -n auto` on a `[dev]`-only venv
produces 17 failures and 1 collection error attributable solely to absent
optional packages — 18 of the run's 261 failure blocks:

| Missing module | Extra | Failing tests | Kind |
|---|---|---|---:|
| `statemachine_engine` | `fsm` | 5 | no guard |
| `feedparser` | `digest` | 4 | no guard |
| `bs4` | `websearch` | 1 (collection error) | no guard |
| `fastapi`, `uvicorn`, `starlette` | `openai-proxy`, `examples-dungeon-master` | 5 | by design |
| `pyarrow` | `rag` | 1 | by design |
| `litellm` | `replicate` | 1 | by design |
| `unified_planning` | `examples-dungeon-master` | 1 | by design |

Two distinct kinds hide behind one symptom:

**Kind A — no guard (10 tests).** The test imports a module that raises when an
extra is absent. `.chaplain/graphs/world_distill/tools.py:17-22` is the honest
version of the failure — it catches `ImportError` and re-raises with the fix
("`world_distill` requires 'feedparser'"). The production module is right to
refuse to load. The *test* is wrong to treat that refusal as a failure:

```
tests/unit/test_world_distill.py::test_write_context_dated_header
E   ModuleNotFoundError: No module named 'feedparser'
```

**Kind B — by design (8 tests).** `test_rag_extra_imports[pyarrow]`,
`test_openai_proxy_extra_imports[fastapi]` and friends exist precisely to
assert an extra imports. They *should* fail when the extra is absent — but only
when the runner claims to have installed it. Today they fail identically to
Kind A, so the two are indistinguishable in the log.

### Why this survives

CI installs every extra
(`dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master,otel,vision`),
so both kinds are always green there. Only a contributor following the
documented `pip install -e ".[dev]"` sees them, and the failure text names a
third-party package rather than the install command that fixes it. The one
counter-example — `core-test` omitting `otel` — proves the principle is known
and applied to a single extra.

## Ideal Result

Running the suite on any documented install produces failures that are all
real. Every test that needs an optional extra either skips with a reason naming
the extra and the install command, or is declared as an extra-import witness
that CI runs with the extra present. A contributor reading the summary line can
tell "3 skipped: fsm extra absent" from "3 failed", and a CI job proves the
distinction holds rather than trusting it.

## Proposed Solution

1. **Guard Kind A at the import boundary.** Module-level
   `pytest.importorskip("feedparser", reason="digest extra: pip install -e '.[digest]'")`
   in the affected test modules, following FR-225's confirmed pattern. Ten
   tests across `test_world_distill.py`, the `statemachine_engine` consumers,
   and `test_fi_domain_crawl.py`.
2. **Mark Kind B explicitly.** Give the `*_extra_imports` witnesses a marker
   (`@pytest.mark.extra("rag")`) so their intent is legible in the log and they
   can be deselected by a contributor who has not installed the extra.
3. **Prove it once in CI.** Extend the existing `core-test` job — already the
   deliberately-incomplete install — to run the full non-slow unit suite with
   `-m "not extra"` and require zero failures. That converts today's convention
   into the gate `detection_without_enforcement` demands.

Not authorized: adding any package to the `[dev]` extra to make failures go
away; changing production import behaviour (`world_distill`'s loud refusal is
correct); a Windows job; skipping tests for any reason other than an absent
optional module.

## Acceptance Criteria

- [ ] AC-01 On a venv installed with exactly `pip install -e ".[dev]"`, `pytest tests/unit/ -q --no-cov -m "not slow and not extra"` reports zero failures and zero collection errors attributable to `ModuleNotFoundError`.
- [ ] AC-02 Each of the 10 Kind A tests skips with a reason string naming both the missing module and the extra that provides it.
- [ ] AC-03 Every `*_extra_imports` witness carries the `extra` marker, registered in `pyproject.toml`, and still fails (not skips) when its extra is claimed to be installed.
- [ ] AC-04 The `core-test` CI job runs the deselected suite and blocks on failure; its existing `otel` assertion is unchanged.
- [ ] AC-05 A test asserts that no test module imports an optional-extra module at module scope without a guard, so the class cannot silently return.
- [ ] AC-06 RED before GREEN in separate commits; `type: fix` changelog fragment; CAP/REQ allocated; diary entry with a `Seed:`.

## Alternatives Considered

| # | Mechanism | Benefit | Objection | Disposition |
|---|---|---|---|---|
| A1 | `pytest.importorskip` at module scope + `extra` marker + `core-test` gate | Precedented (FR-225), skips are visible, and the gate makes the convention enforceable | Ten files to touch; a marker taxonomy to maintain | **Chosen** |
| A2 | Move the packages into `[dev]` | One-line fix, suite goes green everywhere | Makes the documented minimum install heavier for everyone and destroys the `core-test` signal that optional means optional | Rejected |
| A3 | `--continue-on-collection-errors` / broad `--ignore` list | Zero code change | Hides Kind A and Kind B alike, including real import breakage | Rejected: suppression, not normalization |
| A4 | A `conftest.py` hook auto-skipping any test whose import fails | One chokepoint, no per-file edits | Cannot distinguish an absent extra from a genuine broken import — the exact plausible-wrong-answer this repo forbids | Rejected |
| A5 | Document "install all extras before running tests" in CLAUDE.md | Free | An instruction the contributor must remember is not a boundary; the same argument FR-951 used to reject `PYTHONUTF8` guidance | Rejected |

**Strongest dissent (A2).** If every extra is installed in CI and by every
maintainer, the distinction between core and optional is already fiction, and
A2 makes the fiction honest for one line of config. It is rejected because
`core-test` exists specifically to keep that distinction real, and FR-759
already paid for that signal.

**`is_this_a_graph`?** No. No per-item model call, no multi-stage LLM pipeline,
no fan-out — this is a test-marker change plus a CI step.

## Related

- `.chaplain/graphs/world_distill/tools.py:17-22` — the loud production refusal that a test misreads as a failure
- `tests/unit/test_example_extra_imports.py`, `tests/unit/test_fi_domain_crawl.py`, `tests/unit/test_world_distill.py`
- `.github/workflows/workflow.yml` — the `core-test` job
- Diagnostic log: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` on 2026-09-02, `277 failed, 6100 passed, 18 errors`; 18 of the 261 failure blocks in this class
