# Judgement: FR-982 the unit suite must not run with the operator's LangSmith tracer live

> **Human override (2026-09-04): APPROVED WITH REVISIONS, not SPLIT.**
> The graph judge (gpt-5.6-sol, sole route, draft
> `tmp/draft-judgement-copilot-FR-982-unit-suite-runs-with-tracer-live.md`)
> rendered SPLIT on R-1 (separate D-2, the FR-960 argv-dispatch stub,
> into its own FR). The operator declined the split: D-1 and D-2 are the
> two layers of ONE incident — the leak and the seam the leak exposed —
> both under `tests/`, 0.5 days total, and AC-04's "D-1 alone turns the
> test green before D-2" is the RED/GREEN proof trail, not evidence of
> independence worth a second pipeline pass. D-2 stays in scope under
> REQ-YG-642 (CAP-211). R-2, R-3 and R-4 are retained verbatim and were
> folded into the FR on the same day. No re-judgement; authority is
> granted below on the folded FR.

**Verdict:** APPROVED WITH REVISIONS — a real, evidenced test-process boundary defect fixed at the right boundary with no production change; authority activates once R-2 through R-4 are folded into the FR (done 2026-09-04, see Human override).

**Reviewed against:** `feature-requests/FR-982-unit-suite-runs-with-tracer-live.md`; `feature-requests/research-briefs/fr982-unit-suite-traces-live-brief.md`; `feature-requests/FR-960-claude-judge-variant.md`; `feature-requests/FR-960-claude-judge-variant.judgement.md`; `feature-requests/FR-140-clean-git-env-test-fixture.md`; `feature-requests/FR-112-inception-provider.md`; `feature-requests/FR-432-dotenv-upward-search.md`; `feature-requests/FR-720-close-trace-spans-on-loser-cancel.md`; `feature-requests/FR-139-enforce-worktree-bare-corruption-guard.md`; `tests/conftest.py`; `tests/unit/test_fr960_claude_judge_variant.py`; `tests/unit/test_fr720_span_closure.py`; `yamlgraph/config.py`; `yamlgraph/__init__.py`; `pyproject.toml`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `ARCHITECTURE.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

**Prior art:** FR-960 (introduced the failing test; its argv contract is preserved), FR-140/CAP-41 (`_clean_git_env` — the exact session-boundary precedent), FR-112 (claimed provenance of the `_POLLUTING_ENV_VARS` pop; see R-4), FR-432 (owns `load_dotenv`; inherited), FR-720 (opt-in tests that must survive), FR-139 (dismissed, different boundary). REJECTED-FR sweep returned nothing.

## What is sound

The defect is concrete and operationally significant. The FR names a first consumer and exact event, records a local/CI divergence, captures the extra subprocess call chain, and quotes two LangSmith runs carrying the test's literal stub inputs (`FR-982:8-13,67-127`). That establishes both consequences rather than inferring a trace leak from the single red test.

The boundary choice is architecturally sound. `yamlgraph.config` loads `.env` at import (`FR-982:46-56`; `yamlgraph/config.py:42-44`), while the existing conftest guard removes only `LANGCHAIN_TRACING` after each test (`FR-982:129-136`; `tests/conftest.py:28-47`). Overriding all recognized aliases to `"false"` for the pytest session follows the established `_clean_git_env` normalization pattern and survives later non-overwriting dotenv loads (`FR-982:150-181`; `FR-140:31-55`). No production change is necessary.

The research record is substantive despite the recorded research-route outage. It dispositions eight solution classes with executed probes, precedent, effort/risk, and an explicit `is_this_a_graph: no` answer (`FR-982:14-24,255-272`). Prior art, including the rejected-FR sweep, is explicitly dispositioned (`FR-982:25-42`). This is not measurement tooling, so the raw-output-read gate does not apply.

Measurability and feasibility are strong: the four environment values, both tracing predicates, teardown restoration, removal of the weaker guard, production-tree diff, requirement registry, and targeted/full-suite commands are mechanically checkable (`FR-982:206-253`). The strategic classification is **contrib/internal test enforcement**, not a framework primitive: it has one repository test-suite consumer and uses existing pytest and environment-normalization abstractions.

## Required revisions

### R-1: Separate tracing hermeticity from FR-960 mock hardening — OVERRIDDEN

The graph judge required D-2 to be filed as a separate FR. **Overridden by the operator (see header).** D-2 remains in FR-982 scope, under REQ-YG-642. The RED/GREEN discipline the judge wanted is preserved by AC-04 (D-1 alone greens the test) and AC-06 (D-2's own seam witness).

### R-2: Make tracing opt-in respect the declared alias precedence

Replace AC-03. The proposed session fixture sets all four aliases to `"false"` (`FR-982:153-176,206-210`), but AC-03 changed only lower-priority `LANGSMITH_TRACING` (`FR-982:215-218`) while the FR itself declares `LANGSMITH_TRACING_V2` and `LANGCHAIN_TRACING_V2` higher priority (`FR-982:129-133`). That witness cannot establish the claimed transition.

Verified at fold time: `langsmith.utils.get_env_var` is `@functools.lru_cache(maxsize=100)`, so `tracing_is_enabled()` memoizes its first environment read per `(name, default)` key. The opt-in witness must set the highest-priority `LANGSMITH_TRACING_V2=true`, call `langsmith.utils.get_env_var.cache_clear()` so test order cannot determine the result, assert both tracing predicates become truthy, and restore the disabled state (clearing the cache again) afterward. The D-1 session fixture must likewise clear the cache after setting the overrides. Keep the existing FR-720 REQ-YG-547 tests green; those tests deliberately mutate `LANGCHAIN_TRACING_V2` and remove tracing variables (`tests/unit/test_fr720_span_closure.py:49-57,132-139`).

### R-3: Make the live witness prove the stated no-emission claim

Replace the three-signature filter in AC-08 (`FR-982:236-240`) with an isolated-project witness. Run the non-slow unit suite with `.env` tracing enabled and a unique, recorded `LANGSMITH_PROJECT` for the witness, record the tested commit SHA and exact start/end timestamps, then assert the project has zero root runs after client flushing/settling. Checking only `boom_tool`, `fail_tool`, and one `fr_path` does not prove the Ideal Result's broader claim that the suite "sends nothing to LangSmith" (`FR-982:138-142`).

### R-4: Correct the FR-112 evidence attribution

Do not cite `feature-requests/FR-112-inception-provider.md` as if that FR specifies the conftest tracing guard: the cited FR is an Inception provider proposal and contains no such test-environment contract. Attribute the historical commit only if a committed diff/witness is cited; otherwise cite the current `tests/conftest.py` guard as the evidence and describe FR-112 merely as claimed provenance. Preserve the useful distinction that the current guard covers only `LANGCHAIN_TRACING` (`tests/conftest.py:28-47`; `FR-982:129-136`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/conftest.py` — session-scoped autouse `_tracing_off` fixture (four aliases → `"false"`, `get_env_var.cache_clear()`, restore on teardown); removal of `_prevent_env_pollution` / `_POLLUTING_ENV_VARS` |
| D-2 | `tests/unit/test_fr960_claude_judge_variant.py` — `_claude_cli` argv-dispatching `subprocess.run` stand-in; routing test assertions byte-identical |
| D-3 | `tests/unit/test_fr982_tracing_off_in_tests.py` — AC-02/AC-03 witnesses (REQ-YG-644) and AC-06 seam witness (REQ-YG-642) |
| D-4 | `capabilities/CAP-261-tracing-off-in-tests.yaml` registering REQ-YG-644; regenerated `ARCHITECTURE.md` |
| D-5 | One `fix` changelog fragment; one FR-982 diary entry |

Not authorized: production changes under `yamlgraph/`; changes to `yamlgraph.config` dotenv behavior; LangSmith endpoint substitution; CI tracing enablement; tracer warm-up hacks; provider-specific behavior; judge/review graphs, prompts, wrappers, doctrine, or permissions; real Claude or Copilot CLI execution from pytest; changes to any FR-960 routing assertion; any requirement-ID reuse without checking current `origin/main`.

## Revised acceptance criteria

- [ ] AC-01: A session-scoped autouse boundary in `tests/conftest.py` saves all four prior tracer values, overrides `LANGSMITH_TRACING_V2`, `LANGCHAIN_TRACING_V2`, `LANGSMITH_TRACING`, and `LANGCHAIN_TRACING` to `"false"` before test bodies execute, clears `langsmith.utils.get_env_var`'s cache, and restores absence or exact prior values at teardown.
- [ ] AC-02: `tests/unit/test_fr982_tracing_off_in_tests.py` asserts all four variables equal `"false"`, `langsmith.utils.tracing_is_enabled()` is `False`, and `langchain_core.tracers.context._tracing_v2_is_enabled()` is falsy.
- [ ] AC-03: An order-independent witness sets highest-priority `LANGSMITH_TRACING_V2=true`, clears `get_env_var`'s cache, observes both tracing predicates become truthy, and restores the disabled state; the existing REQ-YG-547 FR-720 tests pass.
- [ ] AC-04: RED first: on `main` `6f360e55` with `.env` tracing on, `pytest tests/unit/test_fr960_claude_judge_variant.py -p no:randomly` fails (1 failed, 11 passed) with no command-line env override; after D-1 alone it passes with D-2 not yet applied. Both runs recorded in the Implementation Status.
- [ ] AC-05: The FR-960 routing test stubs `subprocess.run` with the argv-dispatching `_claude_cli`; every existing assertion in `test_claude_backend_visits_only_judge_claude_with_four_tools` is byte-identical.
- [ ] AC-06: Seam witness: feeding `_claude_cli` the sequence `["uname","-p"]`, `["file","-b","x"]`, `["claude","--version"]`, `["file","-b","x"]`, `["claude","auth","status"]`, `["claude","-p","…"]` returns the three responses to the three `claude` calls in order and `returncode == 0` with `bytes` stdout for the others.
- [ ] AC-07: `_prevent_env_pollution` and `_POLLUTING_ENV_VARS` are removed from `tests/conftest.py` only after AC-01 through AC-03 prove the stronger boundary covers their responsibility.
- [ ] AC-08: With `.env` tracing enabled and a unique recorded `LANGSMITH_PROJECT`, `pytest tests/unit -q --no-cov -m "not slow" -n auto` passes; after settling/flushing, a LangSmith query reports zero root runs in that project. The Implementation Status records commit SHA, command, project identifier, timestamps, query, and result.
- [ ] AC-09: `git diff --stat main -- yamlgraph/` is empty.
- [ ] AC-10: `capabilities/CAP-261-tracing-off-in-tests.yaml` registers REQ-YG-644 (`fr: FR-982`, modules `tests/conftest.py`, `tests/unit/test_fr982_tracing_off_in_tests.py`); `ARCHITECTURE.md` regenerated; AC-02/AC-03 tests carry `@pytest.mark.req("REQ-YG-644")`; the AC-06 seam test carries `REQ-YG-642`; `python scripts/req_coverage.py --strict` exits 0; IDs re-verified against `origin/main` at push time.
- [ ] AC-11: The new witness tests are committed RED before the implementation commit and fail because tracing aliases are not normalized (or because the stub is positional), not because of an import error, missing fixture, network call, or unavailable credential.
- [ ] AC-12: A `fix` changelog fragment names FR-982 and REQ-YG-644; the FR-982 diary entry exists with a `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Normalize at the pytest process boundary only; no production code changes and no changes to FR-960 routing assertions. | GATE |
| C-2 | The opt-in witness must use `LANGSMITH_TRACING_V2` and clear the `get_env_var` cache so it is independent of test order. | GATE |
| C-3 | The live witness must use an isolated `LANGSMITH_PROJECT` and prove zero emitted root runs, not merely absence of three known signatures. | GATE |
| C-4 | RED (witness tests) and GREEN (D-1, then D-2) are separate commits; D-1's GREEN commit must precede D-2's so AC-04's "D-1 alone" claim is in git log. | GATE |
| C-5 | REQ-YG-644 / CAP-261 re-verified against `origin/main` immediately before push (cap-req allocation race). | GATE |

Authority granted: implement D-1 through D-5 as frozen above, on the folded FR, RED-first, with no production change.
