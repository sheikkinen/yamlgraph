# Judgement: FR-1154 Omit Sampling Parameters When the Anthropic API Version Removed Them

**Prior art:** [FR-1154-anthropic-api-version-sampling-removed.md](FR-1154-anthropic-api-version-sampling-removed.md) — the FR this judgement rules on, not precedent; dismissed; its own Prior art line dispositions FR-1146, FR-455 and FR-071. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `scripts/judge.sh` (copilot, gpt-5.6-sol), 2026-10-30, round 1.)

**Verdict:** APPROVED WITH REVISIONS — the API-version guard is the minimal provider-boundary fix, but authority activates only after R-1 through R-3 make the proposed branch executable and its version, failure, and regression contracts directly testable.

**Reviewed against:** `feature-requests/FR-1154-anthropic-api-version-sampling-removed.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-1146-anthropic-temperature-deprecated.md`; `feature-requests/FR-1146-anthropic-temperature-deprecated.judgement.md`; `feature-requests/FR-455-reasoning-model-temperature-guard.md`; `feature-requests/FR-071-thinking-budget-graph-level.md`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/utils/llm_providers.py`; `tests/unit/test_llm_factory.py`; `pyproject.toml`; `constraints/dev-py312.txt`; `ARCHITECTURE.md`.

## What is sound

The problem and causal boundary are evidenced. The FR records the dependency transition, the SDK default-header values, LangChain's SDK-2 `extra_body` payload, and a live matrix in which omission succeeds while both `temperature=0.7` and the FR-071 forced `1` fail under API `2026-10-21` (`FR-1154:44-79`). This directly explains why the existing per-model guard is insufficient: current `create_llm()` forces thinking temperature before model selection and exempts the five FR-1146 prefixes from omission (`llm_factory.py:175-217`), while FR-1146 intentionally froze those accepting prefixes under the older API contract (`FR-1146:121-169`).

Scope and single responsibility are sound. The proposal changes one Anthropic request-construction decision, preserves the OpenAI FR-455 branch, refuses a dependency pin, and excludes `top_p`/`top_k` because there are no senders in `yamlgraph/utils/` (`FR-1154:87-95,150-160,188-208`). A consumer-only model change would leave allowlisted 4.x and thinking-enabled calls broken (`FR-1154:190-193`), so the shared factory seam is the smallest sufficient surface.

Feasibility and architecture alignment are established. `anthropic` and `langchain-anthropic` are direct core dependencies (`pyproject.toml:25-28`); the current development constraints preserve the old-header regression floor (`constraints/dev-py312.txt:23,72`); and the cache key is already computed after both the thinking and model guards (`llm_factory.py:175-234`). Reading the installed SDK's public default header follows the repo's provider-boundary normalization rule rather than keying on an SDK-major proxy (`FR-1154:51-65,202-208`; `.github/copilot-instructions.md:43-49,192`). The research record is substantive: it names the first consumer, dispositions five genuine alternatives, distinguishes three prior FRs, and answers `is_this_a_graph` (`FR-1154:7-23,197-208`).

Strategic classification: **Framework primitive correction**. The defect affects the shared synchronous factory used across models and node callers; neither an example nor pattern documentation can prevent the provider 400. Testability is strong once revised: payload inspection already exists for both top-level and SDK-2 `extra_body` temperature (`tests/unit/test_llm_factory.py:570-600`), and the existing suite supplies regression shapes for accepted models, thinking precedence, caching, logs, and non-Anthropic behavior (`tests/unit/test_llm_factory.py:602-672`; `ARCHITECTURE.md:642`).

The direction is not immediately approvable because the proposed branch logs `{version}` without binding that name (`FR-1154:138-146`), AC-04 simultaneously says the FR-1146 tests are unchanged and that their setup is changed to pin the version (`FR-1154:172-174`), and no criterion distinguishes `>= 2026-10-21` from equality or proves the stated missing-header/read-once contracts (`FR-1154:89-94,104,152-154,164-186`).

## Required revisions

### R-1: Bind and reuse the observed API version

Replace the proposed condition with one Anthropic-only read into a local variable, compare that variable to `ANTHROPIC_SAMPLING_REMOVED_API_VERSION`, and use the same variable in the info log. The folded solution must not reference the undefined `version` name and must not call `_anthropic_api_version()` for non-Anthropic providers.

The mechanically sufficient shape is:

```python
anthropic_api_version = (
    _anthropic_api_version() if selected_provider == "anthropic" else None
)
if (
    anthropic_api_version is not None
    and anthropic_api_version >= ANTHROPIC_SAMPLING_REMOVED_API_VERSION
):
    logger.info(
        "Omitting temperature: Anthropic API %s removed sampling parameters",
        anthropic_api_version,
    )
    temperature = None
    temperature_overridden = False
elif <FR-1146 guard, unchanged>:
    ...
```

### R-2: Close the API-version and regression test matrix

Replace AC-04's contradictory "tests pass unchanged" wording with an exact contract: preserve the existing FR-1146 assertions and model matrix, but add deterministic old-version setup so those tests do not depend on the installed SDK.

Add acceptance witnesses for all stated branches:

1. Exact threshold `2026-10-21` omits temperature.
2. A later ISO date such as `2027-01-01` also omits temperature, proving `>=` rather than equality.
3. `2023-06-01` preserves the FR-1146 model rule, including accepted-model temperature, rejecting-model omission, and the FR-071 forced `temperature=1`.
4. A missing `anthropic-version` key raises `KeyError`; no fallback or guessed version is allowed.
5. `_anthropic_api_version()` reads the public SDK header once per process, and non-Anthropic construction does not consult it.

### R-3: Make the SDK-2 witness reproduce the full promised path

Expand AC-07 to require the scratch-venv record to include the exact command, `anthropic` and `langchain-anthropic` versions, and payload output for `claude-haiku-4-5` both without thinking and with `thinking_budget=1024`. In both payloads, temperature must be absent at the top level and from `extra_body`; the thinking payload must retain `{"type": "enabled", "budget_tokens": 1024}`. Fold the transcript into the FR's Implementation Status before enforcement is declared complete.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/llm_factory.py`: add the removal-version constant, cached public-header reader, Anthropic-only local version binding, version-first omission branch, exact info log, and suppression of the superseded FR-071 warning |
| D-2 | `tests/unit/test_llm_factory.py`: RED-first REQ-YG-010 threshold, future-version, old-version, thinking, logging, fail-loud, read-once, cache, and provider-isolation witnesses |
| D-3 | `feature-requests/FR-1154-anthropic-api-version-sampling-removed.md`: fold R-1 through R-3, record the SDK-2 scratch witness, implementation status, decisions, and deviations |
| D-4 | `changelog/unreleased/fr-1154-anthropic-api-version-sampling-removed.md`: one fix fragment with `scope: llm` and `req: REQ-YG-010` |

Not authorized: dependency pins or upgrades; overriding the `anthropic-version` header; keying on `anthropic.__version__`; changes to FR-1146's five-prefix tuple; changes to FR-455; new `top_p`/`top_k` configuration; retry-on-400 behavior; network calls for version discovery; generalized provider capability machinery; graph or prompt edits; consumer-repository changes; new capability or requirement IDs.

## Revised acceptance criteria

- [ ] AC-01: With `_anthropic_api_version()` returning `2026-10-21`, every FR-1146 accepting prefix and `claude-haiku-5-5` produce request payloads with no `temperature` key at the top level or in `extra_body`.
- [ ] AC-02: With `_anthropic_api_version()` returning `2027-01-01`, `claude-haiku-4-5` also omits temperature, proving the branch applies to every ISO API date at or above the threshold.
- [ ] AC-03: At `2026-10-21`, `thinking_budget=1024` retains the enabled thinking payload and omits temperature; exactly one INFO record names `2026-10-21`, and no "Temperature overridden" warning is emitted.
- [ ] AC-04: With `_anthropic_api_version()` returning `2023-06-01`, the existing FR-1146 assertions and model matrix retain their behavior: accepting prefixes preserve temperature, rejecting models omit ordinary temperature, and the FR-071 thinking override retains `temperature=1`. The class has deterministic old-version setup.
- [ ] AC-05: Without patching, `_anthropic_api_version()` equals `anthropic.Anthropic(api_key=...).default_headers["anthropic-version"]`; repeated calls construct/read the SDK client once per process.
- [ ] AC-06: If the SDK default headers lack `anthropic-version`, `_anthropic_api_version()` raises `KeyError`; no fallback value is returned.
- [ ] AC-07: Non-Anthropic providers do not call `_anthropic_api_version()`, preserve current temperature behavior, and the FR-455 tests remain unchanged.
- [ ] AC-08: A recorded scratch-venv run on `anthropic==2.3.0` and `langchain-anthropic==1.7.7` shows `claude-haiku-4-5` payloads without temperature both normally and with `thinking_budget=1024`; the latter retains the enabled thinking field. The FR records the command, versions, and payloads.
- [ ] AC-09: Every new test carries `@pytest.mark.req("REQ-YG-010")`; failing witnesses precede production implementation in git history.
- [ ] AC-10: `.venv/bin/python -m pytest tests/unit/test_llm_factory.py -q --no-cov`, `.venv/bin/python -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto`, and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-11: `changelog/unreleased/fr-1154-anthropic-api-version-sampling-removed.md` has `type: fix`, `scope: llm`, `req: REQ-YG-010`, and describes API-version-driven Anthropic temperature omission.
- [ ] AC-12: The FR records the folded judgement revisions and, after enforcement, the scratch witness, implementation status, decisions, and deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 and the revised acceptance criteria into the FR before production implementation begins. | GATE |
| C-2 | Read the version only from the installed Anthropic SDK's public `default_headers["anthropic-version"]`; missing data must raise, and no SDK-major proxy, pin, header override, or guessed fallback is permitted. | GATE |
| C-3 | Apply API-version omission after the FR-071 override and before the FR-1146 model guard and cache key; at API `>= 2026-10-21`, omission wins over both the model allowlist and forced `temperature=1`. | GATE |
| C-4 | For API versions below `2026-10-21`, preserve the FR-1146 and FR-071 behavior exactly; preserve FR-455 and every non-Anthropic provider path. | GATE |
| C-5 | Commit failing REQ-YG-010 witnesses before GREEN implementation and satisfy the targeted tests, fast unit suite, strict requirement coverage, and recorded SDK-2 scratch witness. | GATE |
| C-6 | Any need for dependency changes, header overrides, additional sampling parameters, retries, generalized capability machinery, or consumer changes stops enforcement and returns as a separate FR. | GATE |

Authority granted: after R-1 through R-3 are folded, implementation may add the cached Anthropic API-version boundary guard, its exact regression witnesses, the SDK-2 evidence record, and the named changelog fragment.
