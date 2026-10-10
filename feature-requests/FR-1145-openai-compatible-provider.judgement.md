# Judgement: FR-1145 Generic OpenAI-Compatible Provider

**Verdict:** APPROVED WITH REVISIONS — the generic provider is a justified, pattern-aligned framework primitive, but authority activates only after the FR closes its research and scope ambiguities and freezes every registry-derived test and documentation contract.

**Reviewed against:** `feature-requests/FR-1145-openai-compatible-provider.md`; `feature-requests/FR-112-inception-provider.md`; `feature-requests/FR-130-inquisitor-architecture-count.md`; `feature-requests/FR-137-deepseek-provider.md`; `feature-requests/FR-277-watcher2-baseline-checkpointing.md`; `feature-requests/FR-408-runtime-repair-metadata.md`; `feature-requests/FR-680-provider-dispatch-registry.md`; `feature-requests/FR-713-persistent-bridge-loop.md`; `feature-requests/FR-766-runpod-provider.md`; `feature-requests/FR-766-runpod-provider.judgement.md`; `feature-requests/FR-1068-default-max-concurrency.md`; `docs/plan-research-runpod.md`; `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/llm_factory.py`; `yamlgraph/config.py`; `tests/unit/test_runpod_provider.py`; `tests/unit/test_fr680_provider_registry.py`; `tests/unit/test_architecture_provider_count.py`; `tests/unit/test_fr708_client_timeout.py`; `tests/unit/test_fr710_deadline_floors.py`; `tests/unit/test_config.py`; `tests/unit/test_root_readme_accuracy.py`; `ARCHITECTURE.md`; `capabilities/CAP-139-root-readme-accuracy-contract.yaml`; `.env.sample`; `README.md`; `CLAUDE.md`; `reference/getting-started.md`; `reference/graph-yaml.md`; `reference/cli.md`; `reference/development-operations.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

**Prior art:** [FR-766-runpod-provider.judgement.md](FR-766-runpod-provider.judgement.md) — its R-1/R-2 fail-fast and fingerprint rulings are inherited unchanged by the shared helper; [FR-1054-nested-object-schemas-reach-the-provider.judgement.md](FR-1054-nested-object-schemas-reach-the-provider.judgement.md) — schema dialect delivery, not provider construction; dismissed; [FR-823-hosted-declarative-graph-runner.judgement.md](FR-823-hosted-declarative-graph-runner.judgement.md) — hosting a graph runner, not an LLM endpoint; dismissed; [FR-1125-refuse-unconstrained-objects-anthropic.judgement.md](FR-1125-refuse-unconstrained-objects-anthropic.judgement.md) — Anthropic schema refusal; dismissed. (Added by the FR author at filing to satisfy the FR-738 gate; not judge output.)

## What is sound

The scope has a concrete consumer and event: an operator running an EU-resident OpenAI-compatible endpoint through `provider: openai_compatible`, with the live Scaleway run as completion witness (`feature-requests/FR-1145-openai-compatible-provider.md:7-10`). The problem is real rather than speculative: the two available mechanisms either mislabel a RunPod factory and prevent two independently configured endpoints in one process, or let `OPENAI_BASE_URL` process-wide state alter the real OpenAI provider without joining its cache fingerprint (`feature-requests/FR-1145-openai-compatible-provider.md:43-66`).

The proposed implementation conforms before extending. RunPod already proves the exact `ChatOpenAI(model, temperature, base_url, api_key, **_bounded(...))` boundary, including explicit errors for endpoint, key, and model (`yamlgraph/utils/llm_providers.py:301-325`), while the provider registry makes a new provider one factory entry rather than a dispatch branch (`yamlgraph/utils/llm_providers.py:329-370`; `feature-requests/FR-680-provider-dispatch-registry.md:33-68`). Extracting that body into one helper preserves the named RunPod preset and avoids cloning a factory into a module already at 439 of 450 lines (`feature-requests/FR-1145-openai-compatible-provider.md:68-77`, `103-140`). No new dependency, YAML surface, graph artifact, plugin API, or provider-specific fallback is needed.

The cache design follows the governing invariant rather than inventing a carve-out. FR-713 requires a uniform declarative fingerprint for every environment value read by a constructor (`feature-requests/FR-713-persistent-bridge-loop.md:374-382`, `395-402`), and the current cache already includes the selected model separately (`yamlgraph/utils/llm_factory.py:185-199`). Therefore `OPENAI_COMPATIBLE_API_KEY` and `OPENAI_COMPATIBLE_BASE_URL` belong in the provider fingerprint while `OPENAI_COMPATIBLE_MODEL` does not.

The strategic classification is **framework primitive**: Scaleway, OVHcloud, and vLLM-backed Verda are three stated endpoint classes with the same wire contract, while the existing abstraction only fits by lying about provider identity (`feature-requests/FR-1145-openai-compatible-provider.md:43-56`, `209-219`). FR-137 explicitly deferred this primitive until provider count exceeded about twelve; the repository now has twelve (`feature-requests/FR-137-deepseek-provider.md:68-71`; `yamlgraph/utils/llm_factory.py:23-36`). The work is one responsibility: expose an honest generic endpoint provider and deduplicate the already-generic RunPod constructor body.

The core behavior is directly testable. Existing RunPod tests show the seams for exact constructor kwargs, fail-fast configuration, import-time default-model handling, and cache identity (`tests/unit/test_runpod_provider.py:57-157`); registry and architecture tests already expose the hard-coded provider sets that must become thirteen (`tests/unit/test_fr680_provider_registry.py:22-37`; `tests/unit/test_architecture_provider_count.py:23-64`). The live criterion separately witnesses the physical invoke, streaming, and structured-output claims instead of presenting mocks as endpoint validation (`feature-requests/FR-1145-openai-compatible-provider.md:196-200`).

## Required revisions

### R-1: Add the required `is_this_a_graph` research disposition

Add an explicit row or paragraph to the committed research record stating: **No existing YAMLGraph graph fits because this is deterministic provider registration and constructor deduplication, not a per-item LLM evaluation, multi-stage LLM pipeline, or parallel model fan-out; no graph is used.** The in-body table contains seven genuine alternatives and dispositions (`feature-requests/FR-1145-openai-compatible-provider.md:209-219`), but it omits the mandatory `is_this_a_graph` answer required for substantive research evidence (`.github/skills/judge-fr/doctrine.md:116-129`; `.github/copilot-instructions.md:129`).

### R-2: Freeze all runtime-derived test contracts and both fingerprint witnesses

Amend Proposed Solution, Planned Operations, and Acceptance Criteria to include:

1. `tests/unit/test_fr708_client_timeout.py`, adding `openai_compatible` to `_TIMEOUT_PARAM`, `_WRAPPER_PATH`, and `_ENV`; its tests parametrize over every `_PROVIDER_FACTORIES` entry, so registration without those entries fails before exercising the new provider (`tests/unit/test_fr708_client_timeout.py:23-62`, `89-105`).
2. `tests/unit/test_config.py`, allowing both `runpod` and `openai_compatible` to have an intentionally empty default model while still requiring every default to be a string (`tests/unit/test_config.py:63-81`).
3. A cache test for changing `OPENAI_COMPATIBLE_API_KEY` as well as the already-planned base-URL change. Both variables are declared construction inputs and both must satisfy REQ-YG-540's "changing a fingerprinted var yields a new client" contract (`ARCHITECTURE.md:645`; `feature-requests/FR-713-persistent-bridge-loop.md:395-402`). Unchanged environment must remain a cache hit.
4. The full targeted command must include `tests/unit/test_fr708_client_timeout.py` and `tests/unit/test_config.py` in addition to the provider, RunPod, registry, and architecture tests.

`tests/unit/test_runpod_provider.py` remains byte-for-byte unchanged. `tests/unit/test_fr710_deadline_floors.py` requires no edit because its provider sets are deliberately limited to Google, Vertex, and Anthropic (`tests/unit/test_fr710_deadline_floors.py:46-93`).

### R-3: Make every edited or normative provider enumeration truthful

Resolve the second human question by choosing the complete-table option: the `reference/graph-yaml.md` section is titled "Supported Providers" but currently names only eight (`reference/graph-yaml.md:99-112`), so adding only the thirteenth provider would knowingly preserve a false exhaustive surface. Amend scope and acceptance criteria to require all thirteen identifiers in that table.

Also freeze these directly coupled surfaces:

- `.env.sample` `Options:` list and new `OPENAI_COMPATIBLE_*` block (`.env.sample:43-56`);
- `reference/development-operations.md` three variable rows and exact `PROVIDER` list (`reference/development-operations.md:98-134`);
- `ARCHITECTURE.md` both provider counts (`ARCHITECTURE.md:271`, `4084`);
- `reference/getting-started.md` provider count (`reference/getting-started.md:18`);
- `README.md` provider feature list, overview list, and `PROVIDER` row (`README.md:21`, `35`, `229`);
- `tests/unit/test_root_readme_accuracy.py` and `capabilities/CAP-139-root-readme-accuracy-contract.yaml`, whose REQ-YG-317 contract says the root README includes every supported provider but whose expected tuple currently omits even RunPod (`tests/unit/test_root_readme_accuracy.py:11-24`; `capabilities/CAP-139-root-readme-accuracy-contract.yaml:10-20`);
- `reference/cli.md` `PROVIDER` row (`reference/cli.md:188`).

Each exact provider enumeration must contain the same thirteen identifiers as `ProviderType`; order may follow the surface's existing convention. This is completion of the provider-registration contract, not authority for unrelated documentation rewrites.

### R-4: Close the open scope question about the real OpenAI provider

Replace Questions for the human item 1 with a non-binding recommendation to file a separate defect FR for the `openai` provider fingerprint. Keep changes to `_PROVIDER_FINGERPRINT_VARS["openai"]`, `OPENAI_BASE_URL`, and `OPENAI_API_BASE` explicitly out of scope. The current FR already says that defect is out of scope (`feature-requests/FR-1145-openai-compatible-provider.md:170-179`) but then leaves "fold into this FR" open as an option (`feature-requests/FR-1145-openai-compatible-provider.md:229-236`), so the plan is internally ambiguous. This judgement does not authorize absorbing that independent provider defect.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/llm_providers.py`: extract one private OpenAI-compatible endpoint helper; keep `_create_runpod_llm()` as a thin, message-preserving preset; add and register `_create_openai_compatible_llm()`; keep both outside `_THINKING_PROVIDERS`; module remains at or below 450 lines. |
| D-2 | `yamlgraph/utils/llm_factory.py`: add `"openai_compatible"` to `ProviderType` and add `("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL")` to `_PROVIDER_FINGERPRINT_VARS`; do not change the `openai` fingerprint. |
| D-3 | `yamlgraph/config.py`: add `DEFAULT_MODELS["openai_compatible"] = os.getenv("OPENAI_COMPATIBLE_MODEL", "")` with no hard-coded fallback. |
| D-4 | `tests/unit/test_openai_compatible_provider.py`: registration, exact constructor arguments, all three fail-fast errors, unchanged-env cache hit, and distinct clients after either key or base-URL changes. |
| D-5 | Existing provider contract tests: update `tests/unit/test_fr680_provider_registry.py`, `tests/unit/test_architecture_provider_count.py`, `tests/unit/test_fr708_client_timeout.py`, `tests/unit/test_config.py`, and `tests/unit/test_root_readme_accuracy.py`; leave `tests/unit/test_runpod_provider.py` unchanged. |
| D-6 | `tests/integration/test_openai_compatible_provider.py`: credential-gated real invoke, stream with at least two chunks, and Pydantic structured-output round trip against the configured endpoint. |
| D-7 | Provider documentation: `.env.sample`, `reference/development-operations.md`, `reference/graph-yaml.md`, `reference/getting-started.md`, `reference/cli.md`, `README.md`, and the two provider counts in `ARCHITECTURE.md`; exact provider enumerations list all thirteen identifiers. |
| D-8 | Traceability and release record: update `capabilities/CAP-139-root-readme-accuracy-contract.yaml` only as needed to make its provider enumeration truthful; add `changelog/unreleased/fr-1145-openai-compatible-provider.md` with `type: feat` and `req: REQ-YG-010`; tag every new test with the applicable existing REQ. |
| D-9 | Update `feature-requests/FR-1145-openai-compatible-provider.md` with R-1 through R-4, implementation status, the live Scaleway model and per-case result, and any deviation from this frozen scope. |

Not authorized: changing the real `openai` provider's fingerprint or `OPENAI_BASE_URL` behavior; named endpoint profiles or multiple simultaneous `openai_compatible` configurations; retiring or renaming `runpod`; changing any RunPod error text or editing `tests/unit/test_runpod_provider.py`; adding a graph/demo or modifying governed `graph.yaml`/`prompts/*.yaml` artifacts; adding dependencies; adding capability fallbacks, provider-specific retry behavior, thinking-budget semantics, plugin registration, vendor-specific factories, or CI/hook/judge/review doctrine; committing credentials.

## Revised acceptance criteria

- [ ] AC-01: `openai_compatible` appears in `ProviderType`, `DEFAULT_MODELS`, `_PROVIDER_FACTORIES`, and `_PROVIDER_FINGERPRINT_VARS`, and does not appear in either thinking-provider set.
- [ ] AC-02: With all three `OPENAI_COMPATIBLE_*` variables set, `create_llm(provider="openai_compatible")` constructs `ChatOpenAI` with the selected model, requested temperature, `base_url` exactly from `OPENAI_COMPATIBLE_BASE_URL`, `api_key` exactly from `OPENAI_COMPATIBLE_API_KEY`, and existing bounded timeout/retry kwargs; `root_client.base_url` resolves to that URL with the SDK's trailing slash.
- [ ] AC-03: Missing or blank `OPENAI_COMPATIBLE_BASE_URL`, `OPENAI_COMPATIBLE_API_KEY`, or selected model independently raises `ValueError` naming the missing variable and provider `'openai_compatible'` before `ChatOpenAI` is constructed.
- [ ] AC-04: `DEFAULT_MODELS["openai_compatible"]` reads `OPENAI_COMPATIBLE_MODEL` with no hard-coded fallback, remains a string when unset, and an empty selected model is rejected at the provider boundary.
- [ ] AC-05: `_PROVIDER_FINGERPRINT_VARS["openai_compatible"]` is exactly `("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL")`; unchanged environment returns the same cached client, while changing either variable returns a distinct client.
- [ ] AC-06: `_create_runpod_llm()` delegates to the shared helper without changing any RunPod constructor argument or error string; `tests/unit/test_runpod_provider.py` has zero edits and passes.
- [ ] AC-07: `yamlgraph/utils/llm_providers.py` is at most 450 lines and contains one implementation of the env-configured authenticated `ChatOpenAI + base_url` constructor body used by RunPod and `openai_compatible`.
- [ ] AC-08: Registry, architecture, timeout, config, and README contract tests are updated for the thirteenth provider and pass: `tests/unit/test_fr680_provider_registry.py`, `tests/unit/test_architecture_provider_count.py`, `tests/unit/test_fr708_client_timeout.py`, `tests/unit/test_config.py`, and `tests/unit/test_root_readme_accuracy.py`.
- [ ] AC-09: Every exact provider enumeration in `.env.sample`, `reference/development-operations.md`, `reference/graph-yaml.md`, `reference/cli.md`, and `README.md` contains the same thirteen identifiers as `ProviderType`; `reference/getting-started.md` and both `ARCHITECTURE.md` count surfaces say thirteen.
- [ ] AC-10: `tests/integration/test_openai_compatible_provider.py` skips unless all three `OPENAI_COMPATIBLE_*` variables are set; when set, it performs real `invoke()`, `stream()` with at least two non-empty chunks, and `with_structured_output()` against a Pydantic model.
- [ ] AC-11: Before status becomes Completed, the FR records one live Scaleway run with date, model, endpoint class without secrets, and separate pass/fail results for invoke, streaming, and structured output. If credentials are unavailable or any case fails, the FR remains In Progress and records the exact command and result; mocked tests are not presented as live validation.
- [ ] AC-12: No new dependency, vendor-specific fallback, new provider factory beyond `openai_compatible`, graph/demo artifact, or change to the existing `openai` provider fingerprint is present.
- [ ] AC-13: All new tests carry applicable `@pytest.mark.req(...)` markers, `python scripts/req_coverage.py --strict` passes, and `changelog/unreleased/fr-1145-openai-compatible-provider.md` has `type: feat` and `req: REQ-YG-010`.
- [ ] AC-14: The targeted unit command covers the new provider, unchanged RunPod suite, registry, architecture count, timeout matrix, config, and root README contracts and passes; the gated integration command then passes or honestly skips under AC-11.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into `feature-requests/FR-1145-openai-compatible-provider.md` before implementation authority is active. | GATE |
| C-2 | Implement only the shared private `ChatOpenAI + base_url` helper and two thin presets; preserve RunPod behavior and error strings exactly, add no dependency, and keep `openai_compatible` out of thinking-provider sets. | GATE |
| C-3 | Treat every registry-derived test matrix and every normative provider enumeration in D-5 through D-8 as part of the provider addition; do not stop after the four tests named in the original Planned Operations. | GATE |
| C-4 | Do not modify the existing `openai` fingerprint or endpoint semantics under this FR; pursue that defect through a separate judged FR. | GATE |
| C-5 | Do not mark the FR Completed or claim Scaleway support unless the real gated invoke, multi-chunk stream, and structured-output cases ran successfully and their model/results are recorded in the FR. | GATE |
| C-6 | Never commit or print real API keys; integration gates consume credentials only from environment variables. | GATE |
| C-7 | Keep `yamlgraph/utils/llm_providers.py` at or below 450 lines; failure means the helper extraction is incomplete, not authority for an unrelated module refactor. | GATE |

Authority granted after R-1 through R-4 are folded into the FR: implement one generic `openai_compatible` provider through the shared RunPod-shaped constructor boundary, with the frozen tests, truthful provider documentation, and live Scaleway witness above.
