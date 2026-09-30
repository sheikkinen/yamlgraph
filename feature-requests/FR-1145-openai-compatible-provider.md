# Feature Request: FR-1145 Generic OpenAI-Compatible Provider

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — APPROVED WITH REVISIONS, R-1..R-4 folded ([judgement](FR-1145-openai-compatible-provider.judgement.md))
**Requested:** 2026-09-30
**First consumer / first event:** the operator, running a yamlgraph graph
against an EU-resident pay-per-token API (Scaleway Generative APIs, Paris)
— the first `provider: openai_compatible` run, whose live integration
test run is the completion witness.
**Research:** in-body dispositioned alternatives table, see
[Alternatives Considered](#alternatives-considered) (FR-889 style; each
row cites the probe that produced it).
**Prior art:** [FR-137-deepseek-provider.md](FR-137-deepseek-provider.md)
— rejected this exact provider as its alternative 2 "if provider count
exceeds ~12"; the count is now 12 (`ProviderType` in
`yamlgraph/utils/llm_factory.py`), and this FR is that revisit.
[FR-766-runpod-provider.md](FR-766-runpod-provider.md) — already
shipped a generic OpenAI-compatible factory under a vendor name; this FR
extracts its body into one shared helper instead of cloning it a second
time. [FR-112-inception-provider.md](FR-112-inception-provider.md),
FR-137 — fixed-URL named OpenAI-compatible providers; they stay (their
base URL is a constant, not config). [FR-680-provider-dispatch-registry.md](FR-680-provider-dispatch-registry.md)
— the registry this FR adds one entry to. [FR-713-persistent-bridge-loop.md](FR-713-persistent-bridge-loop.md)
— env-fingerprinted cache keys (REQ-YG-540) the new provider must join.
Rejected FRs: a grep of `Status: Rejected` FRs mentioning provider or
`base_url` returns FR-1068, FR-130, FR-277, FR-408 — none proposes a
configurable-endpoint provider; no rejected precedent in this territory.

## Summary

Add one provider, `openai_compatible`, that points `ChatOpenAI` at any
OpenAI-compatible base URL named in env. Extract the body of
`_create_runpod_llm` into a shared helper both providers call, so the
module stays inside its line gate and no factory body is cloned.

## Value Statement

Operators can use any OpenAI-compatible endpoint — EU-resident
pay-per-token APIs in particular — by setting three env vars, without a
new provider FR per vendor and without misusing another vendor's name.

## Problem

Every OpenAI-compatible vendor currently costs a provider FR: xAI,
Inception, DeepSeek, RunPod and LM Studio are five `ChatOpenAI +
base_url` factories. The EU on-demand investigation of 2026-09-30 found
at least three more candidates with the same wire surface — Scaleway
Generative APIs, OVHcloud AI Endpoints, Verda serverless containers
running vLLM — none of which justifies its own factory.

The two workarounds available today are both wrong:

1. `provider: runpod` with `RUNPOD_ENDPOINT=https://api.scaleway.ai/v1`
   works (the factory is generic), but the config lies about the vendor,
   and a graph cannot use RunPod and a second endpoint in one process.
2. `provider: openai` with `OPENAI_BASE_URL` set. Probe (2026-09-30,
   langchain-openai 1.4.1): `ChatOpenAI(model=...)` with
   `OPENAI_BASE_URL=https://api.scaleway.ai/v1` in env resolves
   `root_client.base_url` to `https://api.scaleway.ai/v1/` while
   `openai_api_base` reads `None`. The redirect is invisible in the
   constructed object's own field, it hijacks the real OpenAI provider for
   the whole process, and `_PROVIDER_FINGERPRINT_VARS["openai"]` is
   `("OPENAI_API_KEY",)` — the cache key does not change when the base URL
   does.

Constraint: `yamlgraph/utils/llm_providers.py` is 439 lines against a
450-line maximum. A cloned 25-line factory does not fit.

## Ideal Result

A graph author writes `provider: openai_compatible`, sets
`OPENAI_COMPATIBLE_BASE_URL`, `OPENAI_COMPATIBLE_API_KEY` and
`OPENAI_COMPATIBLE_MODEL`, and gets the same invoke, stream and
structured-output behaviour as `runpod` — with fail-fast on missing
config, an env-fingerprinted cache key, and exactly one implementation of
"ChatOpenAI at a configured endpoint" in the codebase.

## Planned Operations

```yaml
probes:
  - "wc -l yamlgraph/utils/llm_providers.py after the edit — over 450 means the helper extraction is incomplete, not a reason to split the module"
  - "pytest tests/unit/test_runpod_provider.py unchanged and green after extraction — any edit to that file is a behaviour change, back to plan"
  - "grep every exact provider enumeration (R-3 surfaces) — each must name the same 13 identifiers as ProviderType"
  - "live: gated integration test against Scaleway Generative APIs with a real key — invoke, stream, structured output"
branches:
  - "Scaleway rejects json_schema structured output for the chosen model → record the model and error in the FR, pick a model the vendor documents as supporting it; do not add a fallback method"
  - "no Scaleway key available → integration test skips; FR stays In Progress, not Completed"
  - "extraction changes any runpod error message → revert to message-preserving helper arguments"
delegations:
  - "judge.sh: 1 run, 2 if revisions are disputed"
waits:
  - "judge"
  - "operator provides OPENAI_COMPATIBLE_* credentials for the live run"
commands:
  - scripts/judge.sh feature-requests/FR-1145-openai-compatible-provider.md
  - pytest tests/unit/test_openai_compatible_provider.py tests/unit/test_runpod_provider.py tests/unit/test_fr680_provider_registry.py tests/unit/test_architecture_provider_count.py tests/unit/test_fr708_client_timeout.py tests/unit/test_config.py tests/unit/test_root_readme_accuracy.py -q --no-cov
  - pytest tests/integration/test_openai_compatible_provider.py -v
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

### 1. Shared helper, two thin factories (`yamlgraph/utils/llm_providers.py`)

```python
def _openai_compatible(
    provider: str, base_url_var: str, key_var: str, model_var: str,
    model: str, temperature: float, **kwargs: object,
) -> BaseChatModel:
    """ChatOpenAI at an env-configured endpoint; all three inputs fail fast (FR-766 R-1)."""
    from langchain_openai import ChatOpenAI

    base_url = os.getenv(base_url_var)
    if not base_url:
        raise ValueError(f"{base_url_var} is required for provider '{provider}'")
    api_key = os.getenv(key_var)
    if not api_key:
        raise ValueError(f"{key_var} is required for provider '{provider}'")
    if not model:
        raise ValueError(f"{model_var} is required for provider '{provider}'")
    return ChatOpenAI(model=model, temperature=temperature, base_url=base_url,
                      api_key=api_key, **_bounded(dict(kwargs)))


def _create_runpod_llm(model, temperature, **kwargs):
    return _openai_compatible("runpod", "RUNPOD_ENDPOINT", "RUNPOD_API_KEY",
                              "RUNPOD_MODEL", model, temperature, **kwargs)


def _create_openai_compatible_llm(model, temperature, **kwargs):
    return _openai_compatible("openai_compatible", "OPENAI_COMPATIBLE_BASE_URL",
                              "OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_MODEL",
                              model, temperature, **kwargs)
```

The generated error strings equal today's runpod strings byte for byte,
so `tests/unit/test_runpod_provider.py` is the unchanged witness that the
extraction preserved behaviour.

### 2. Registration

- `_PROVIDER_FACTORIES["openai_compatible"]` (not in `_THINKING_PROVIDERS`).
- `ProviderType` gains `"openai_compatible"`.
- `_PROVIDER_FINGERPRINT_VARS["openai_compatible"] =
  ("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL")` — model is
  already in the cache key (FR-766 judgement R-2 precedent).
- `yamlgraph/config.py` `DEFAULT_MODELS["openai_compatible"] =
  os.getenv("OPENAI_COMPATIBLE_MODEL", "")` — no hard-coded default, an
  endpoint serves what it serves.

### 3. Documentation surfaces

- `.env.sample`: an `OPENAI_COMPATIBLE_*` block with Scaleway as the
  example URL, and the `Options:` line.
- `reference/development-operations.md`: three env rows, and the
  `PROVIDER` row. That row today omits `vertex`; since this FR rewrites
  the line, it lists all 13.
- `reference/graph-yaml.md` "Supported Providers" table: completed to
  all 13 providers (it listed 8; judgement R-3).
- `reference/getting-started.md` provider count; `reference/cli.md`
  `PROVIDER` row; `README.md` provider feature list, overview list and
  `PROVIDER` row; `tests/unit/test_root_readme_accuracy.py` and
  `capabilities/CAP-139-root-readme-accuracy-contract.yaml` provider
  enumeration (R-3). Every exact enumeration names the same 13
  identifiers as `ProviderType`.
- `ARCHITECTURE.md`: provider count 12 → 13 in both places (line 271
  diagram, line 4084 module table; the latter guarded by REQ-YG-121).
- Changelog fragment `changelog/unreleased/fr-1145-openai-compatible-provider.md`,
  `type: feat`, `req: REQ-YG-010`.

### 4. Registry-derived test matrices (R-2)

- `tests/unit/test_fr708_client_timeout.py`: add `openai_compatible` to
  `_TIMEOUT_PARAM`, `_WRAPPER_PATH` and `_ENV`.
- `tests/unit/test_config.py`: allow both `runpod` and
  `openai_compatible` an intentionally empty default model.
- Cache witnesses for BOTH fingerprinted vars (key and base URL), plus
  an unchanged-env cache hit.

### Out of scope

- A demo graph. Creating one is governed authoring (`scripts/author.sh`);
  the live integration test is the demonstration witness.
- Multiple simultaneous `openai_compatible` endpoints in one process
  (named profiles). No consumer yet.
- Retiring `runpod`. It keeps its env vars, demo and tests; after this FR
  it is a four-line preset.
- The `openai` provider's `OPENAI_BASE_URL` fingerprint gap (Problem,
  workaround 2). Not authorized here (judgement C-4); a separate defect
  FR is recommended.

## Acceptance Criteria

- [ ] AC-1: `create_llm(provider="openai_compatible")` returns a
      `ChatOpenAI` whose `root_client.base_url` equals
      `OPENAI_COMPATIBLE_BASE_URL` (plus trailing slash) and whose API key
      is `OPENAI_COMPATIBLE_API_KEY`. Unit test, tagged REQ-YG-010.
- [ ] AC-2: each of the three env vars, when unset, raises `ValueError`
      naming that variable and `'openai_compatible'`. Three unit tests.
- [ ] AC-3: changing `OPENAI_COMPATIBLE_BASE_URL` between two
      `create_llm` calls returns a different client object (fingerprint).
      Unit test.
- [ ] AC-4: `tests/unit/test_runpod_provider.py` passes with zero edits
      to that file.
- [ ] AC-5: `wc -l yamlgraph/utils/llm_providers.py` ≤ 450.
- [ ] AC-6: `tests/unit/test_fr680_provider_registry.py` and
      `tests/unit/test_architecture_provider_count.py` pass with 13
      providers.
- [ ] AC-7: `tests/integration/test_openai_compatible_provider.py`,
      skipped unless all three env vars are set, covers invoke, stream (at
      least 2 chunks) and `with_structured_output` against a Pydantic
      model. One live run against Scaleway Generative APIs is recorded in
      this FR (model, pass/fail per case) before status Completed.
- [ ] AC-8: `.env.sample` `Options:` line and the
      `reference/development-operations.md` `PROVIDER` row each list the
      same 13 names as `ProviderType`.
- [ ] AC-9: `python scripts/req_coverage.py --strict` passes; changelog
      fragment present.

Binding acceptance criteria are the judgement's revised AC-01..AC-14
([judgement](FR-1145-openai-compatible-provider.judgement.md#revised-acceptance-criteria));
the list above is superseded where they differ.

## Alternatives Considered

**`is_this_a_graph` (R-1):** No existing YAMLGraph graph fits because
this is deterministic provider registration and constructor
deduplication, not a per-item LLM evaluation, multi-stage LLM pipeline,
or parallel model fan-out; no graph is used.

| # | Alternative | Probe / evidence | Disposition |
|---|---|---|---|
| A1 | Do nothing; use `provider: runpod` with a non-RunPod URL | `_create_runpod_llm` reads only `RUNPOD_*` and passes them to `ChatOpenAI` — works today | Rejected: vendor name lies in config; blocks RunPod plus a second endpoint in one process |
| A2 | Use `provider: openai` + `OPENAI_BASE_URL` | Probe above: `root_client.base_url` follows the env var, `openai_api_base` shows `None`, fingerprint omits it | Rejected: hijacks the real OpenAI provider process-wide; stale cache key |
| A3 | One named provider per vendor (`scaleway`, `ovh`, `verda`) | FR-137's own threshold (~12) is reached; each costs a factory, fingerprint, docs, tests; `llm_providers.py` at 439/450 lines | Rejected: the growth FR-137 anticipated; module gate would force a split per vendor |
| A4 | Clone `_create_runpod_llm` as a second factory | Module is 439 lines; clone is 25 lines → 464 | Rejected: breaks the 450 gate and duplicates a body (Commandment 8) |
| A5 | Replace `runpod` with `openai_compatible` (retire the vendor name) | `examples/demos/hello-runpod/graph.yaml` uses `provider: runpod`; editing it is governed authoring; FR-766 is recent and has a live witness | Deferred: larger blast radius, no consumer asking; the helper makes a later retirement a deletion |
| A6 | Per-node `base_url:` in graph YAML | `grep -rn base_url yamlgraph --include='*.py'` finds it only in `llm_providers.py`; the "Supported Providers" table in `reference/graph-yaml.md` configures endpoints only via env (`LMSTUDIO_BASE_URL`); would touch schema, linter, cache key | Rejected: new YAML surface with no consumer; env config matches all 12 existing providers |
| A7 | LiteLLM (`langchain-litellm`) as universal adapter | Already used for `replicate`, which needs `litellm.drop_params = True` and cannot do structured output (docstring in `_create_replicate_llm`) | Rejected: weaker structured-output path than `ChatOpenAI` json_schema |

## Related

- `yamlgraph/utils/llm_providers.py` — `_create_runpod_llm`, `_PROVIDER_FACTORIES`
- `yamlgraph/utils/llm_factory.py` — `ProviderType`, `_PROVIDER_FINGERPRINT_VARS`
- `docs/plan-research-runpod.md` — earlier RunPod research
- Scaleway Generative APIs docs (OpenAI-compatible, Paris-only hosting,
  json_schema structured outputs)

### Questions for the human

1. Recommendation (non-binding, R-4): file a separate defect FR for
   `provider: openai` ignoring `OPENAI_BASE_URL` / `OPENAI_API_BASE` in
   its cache fingerprint while `ChatOpenAI` honours them (probe in
   Problem). Out of scope here.
2. Resolved by R-3: the `reference/graph-yaml.md` table is completed to
   13 providers.
