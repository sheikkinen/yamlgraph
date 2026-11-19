# Feature Request: FR-1170 Azure Non-Thinking Mode (`thinking_budget: 0`)

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced 2026-11-19 on `docs/fr-1170-azure-thinking-off`; awaiting PR, CI and review
**Effort:** 0.5 days
**Requested:** 2026-11-19
**First consumer / first event:** the CSAP voicebot race
(`terveystalo/customer-service-agent-platform`,
`graphs/flex_navigator/graph_v2.yaml`). That graph sets
`defaults: thinking_budget: 0` and races `provider: azure` candidates with
`temperature: 0.0`. The first event is a race node that includes the Azure
deployment `aaa-gpt-6-luna`. Today that request reaches Azure with thinking on
and `temperature: 0`, and the API rejects it with 400 `unsupported_value`
(param `temperature`), so the candidate loses every race.
**Research:** in-body dispositioned alternatives table, each row with a probe
result. The evidence is CSAP NC-584 (live HTTP probes against the CSAP TEST
Azure AI Services account, 2026-11-19, merged as
`terveystalo/customer-service-agent-platform#884`) plus one offline payload
probe against the installed `langchain-azure-ai` 1.2.9.
**`is_this_a_graph`:** No. This is a one-value mapping at the provider
construction boundary, with no per-item model calls and no LLM pipeline. Its
witness is a request-payload assertion, not an LLM judgement.
**Prior art:**
- [FR-1056-deepseek-thinking-off.md](FR-1056-deepseek-thinking-off.md) is the
  direct precedent. It made DeepSeek map `thinking_budget: 0` to
  `reasoning_effort: "none"` and ignore other values. This FR applies the
  identical contract to `azure`.
- [FR-1148-anthropic-thinking-off.md](FR-1148-anthropic-thinking-off.md)
  is the Anthropic sibling of the same "zero means off" contract. It changes
  only the Anthropic factory; this FR neither supersedes nor extends it.
- [FR-263-azure-openai-provider.md](FR-263-azure-openai-provider.md)
  introduced `_create_azure_llm`; its construction is unchanged apart from
  the new keyword.
- [FR-680-provider-dispatch-registry.md](FR-680-provider-dispatch-registry.md)
  introduced the `_THINKING_PROVIDERS` registry this FR widens.
- [FR-455-reasoning-model-temperature-guard.md](FR-455-reasoning-model-temperature-guard.md)
  drops `temperature` for `o1`/`o3`/`o4` model names. It doesn't apply here,
  because Azure deployment names are chosen by the operator (`aaa-gpt-6-luna`).
- FR-1144 (race thinking A/B on `image-that-speaks`): its
  `FR-1144-No-Thinking.yaml` treatment arm races `azure / aaa-gpt-5.4-mini`
  with `thinking_budget: 0`. Under the current code the Azure arm never
  received that setting. FR-1144 deliberately left Azure untouched, and its
  AC-06 witness `test_vertex_factory_gets_zero_azure_factory_gets_none`
  (`tests/unit/test_race_node.py`) asserts the Azure factory is called with
  `(model, 0.0)`. **FR-1170 supersedes only that expectation:** the witness
  is renamed for the new contract, expects the Azure factory to receive `0`,
  and keeps its Vertex and mixed-candidate assertions and its existing REQ
  mapping. FR-1144's other objection (other Azure deployments may reject
  `reasoning_effort`) is accepted as a loud provider error; see Behaviour
  change. The historical FR-1144 judgement is not edited.

## Summary

`provider: azure` can't be put into non-thinking mode from YAML.
`dispatch_provider` calls `_create_azure_llm` without `thinking_budget`
because `azure` is absent from `_THINKING_PROVIDERS`, so `thinking_budget: 0`
is silently dropped. The fix: map `thinking_budget: 0` to
`reasoning_effort: "none"` for `azure`, exactly as FR-1056 does for DeepSeek.

## Value Statement

Graph authors on Azure reasoning deployments (the gpt-5.x and gpt-6 families)
can turn reasoning off from YAML. This cuts latency, and it makes
`temperature: 0` acceptable to models that reject it while thinking.

## Problem

Three facts, each verified on 2026-11-19:

1. **The knob is silently dropped.** `azure` is not in `_THINKING_PROVIDERS`
   (`yamlgraph/utils/llm_providers.py`), and `_create_azure_llm(model,
   temperature, **kwargs)` has no `thinking_budget` parameter. A node, race or
   graph default with `thinking_budget: 0` therefore has no effect on Azure
   candidates. This is the `plausible_wrong_answer` shape: a setting that
   looks applied and isn't.
2. **On Azure reasoning models, thinking on and `temperature: 0` together are
   rejected.** CSAP NC-584 probe, deployment `aaa-gpt-6-luna`:
   - with default reasoning, `temperature: 0` returned 400 `unsupported_value`
     (param `temperature`);
   - with `reasoning_effort: "none"` and `temperature: 0` the request returned
     200, both alone (N-T0) and with strict `json_schema` output (N-TS).
   The race node forwards its `temperature` to every candidate, so a
   temperature-pinned race can't use these deployments today.
3. **Latency.** In the same probe, `aaa-gpt-6-luna` with default reasoning
   took 1.26–1.98 × the median latency of `aaa-gpt-5.4-mini`, using 16–25
   reasoning tokens. With `reasoning_effort: "none"` it took 1.09–1.26 × and
   used 0 reasoning tokens.

## Ideal Result

An Azure candidate obeys the reasoning switch it appears to have:
- `thinking_budget: 0` sends `reasoning_effort: "none"`;
- omitting it leaves the deployment's API default untouched.

No new YAML field, and no change for any other provider.

## Proposed Solution

### YAML interface (no new field)

```yaml
defaults:
  thinking_budget: 0            # Azure candidates: reasoning_effort "none"

nodes:
  classify_intents:
    type: race
    temperature: 0.0
    candidates:
      - { provider: vertex, model: gemini-3.5-flash-lite }
      - { provider: azure,  model: aaa-gpt-6-luna }
```

### Implementation

1. `llm_providers.py`:
   - add `azure` to `_THINKING_PROVIDERS`;
   - give `_create_azure_llm` a parameter
     `thinking_budget: int | None = None`;
   - set `reasoning_effort="none"` only when `thinking_budget == 0`;
   - for any other non-`None` value, send nothing and log at DEBUG, naming
     the ignored value and the provider (FR-1056 wording).
   - Update the `_THINKING_PROVIDERS` comment to name Azure next to DeepSeek.
2. `llm_factory.py`: no executable behaviour change (AC-09 updates the
   `create_llm` docstring only). `azure` stays out of `THINKING_PROVIDERS`, so
   `thinking_budget >= 1024` on Azure still raises `ValueError`.
3. The cache key already includes `thinking_budget`, so no cache change.
4. The offline probe shows `AzureAIOpenAIApiChatModel` subclasses
   `ChatOpenAI` and has a `reasoning_effort` field. `_get_request_payload`
   emits
   `{'model': 'aaa-gpt-6-luna', 'stream': False, 'temperature': 0.0,
   'reasoning_effort': 'none'}` verbatim. No `extra_body` workaround is needed.

### Behaviour change for existing Azure graphs

Any Azure node that already has `thinking_budget: 0` will start sending
`reasoning_effort: "none"`.
- A deployment that doesn't accept the field fails with a provider 400. The
  failure is loud, not silent. Two remedies, with no change to how defaults
  resolve:
  - remove `thinking_budget: 0` at the level that defines it (node, race or
    graph `defaults:`); removing it from a node alone does not help when the
    zero is inherited from `defaults:`, because an absent node value inherits
    the default (`race_node.py`);
  - or override an inherited zero on that node with an accepted non-zero
    value such as `thinking_budget: 512`, which sends no `reasoning_effort`.
- Known consumers:
  - the CSAP flex navigator (graph default; its Azure candidate is
    `aaa-gpt-5.4-mini`);
  - `examples/demos/image-that-speaks/FR-1144-No-Thinking.yaml` (also
    `aaa-gpt-5.4-mini`).
  Both use the same deployment, which AC-10 witnesses live.
- No other `thinking_budget: 0` in this repository pairs with `azure`
  (`git grep "thinking_budget: 0"` returns 4 files; the other three are
  google/vertex/anthropic demos).

## Acceptance Criteria

*Revised by the judgement (R-1 … R-3 folded 2026-11-19).*

- [x] AC-01: With the LLM cache isolated and dummy `AZURE_AI_ENDPOINT` /
      `AZURE_AI_API_KEY`, `create_llm(provider="azure",
      model="aaa-gpt-6-luna", temperature=0.0, thinking_budget=0)` returns
      `AzureAIOpenAIApiChatModel`, and its request payload contains
      `reasoning_effort == "none"` and `temperature == 0.0`.
- [x] AC-02: The same call with `thinking_budget` omitted produces a payload
      with no `reasoning_effort` key.
- [x] AC-03: The same call with `thinking_budget=512` doesn't raise, omits
      the field, and emits a DEBUG record naming `512` and `azure`.
- [x] AC-04: `thinking_budget=8000` on Azure raises `ValueError` naming the
      supported token-budget providers; Azure stays outside the native-budget
      `THINKING_PROVIDERS` in `llm_factory.py`.
- [x] AC-05: Through a real race node's candidate-construction path (model
      invocation mocked, factory/dispatch real): node-level `0` produces an
      Azure payload with `reasoning_effort == "none"`; node-level `512`
      overriding graph-default `0` produces a payload without the field.
- [x] AC-06: Existing DeepSeek, Anthropic, Google and Vertex thinking
      behaviour is unchanged; omitted, `0` and `512` Azure calls don't alias
      in the cache. The FR-1144 witness
      `test_vertex_factory_gets_zero_azure_factory_gets_none` is renamed and
      expects the Azure factory to receive `0`, keeping its Vertex and
      mixed-race assertions; affected race/provider-dispatch tests pass.
- [x] AC-07: New tests are keyless and carry
      `@pytest.mark.req("REQ-YG-732")`; retained race-forwarding witnesses
      keep their existing REQ mapping; `python scripts/req_coverage.py
      --strict` passes.
- [x] AC-08: `capabilities/CAP-307-azure-non-thinking.yaml` defines
      REQ-YG-732 (zero, omission/accepted non-zero, and unsupported
      token-budget cases), and `ARCHITECTURE.md` is regenerated with
      `scripts/aggregate_capabilities.py`. If those IDs are taken, use the
      next verified free pair consistently and record it here.
- [x] AC-09: `reference/graph-yaml.md` and the `create_llm` docstring state
      the Azure contract: zero disables thinking, omission keeps the API
      default, other accepted values are ignored, `>= 1024` is still
      rejected, and an Azure deployment that doesn't support
      `reasoning_effort` returns a provider error. The guidance explains how
      to override an inherited zero (see Behaviour change).
- [x] AC-10: Record HTTP 200 compatibility evidence for the combined
      `temperature: 0` + `reasoning_effort: "none"` payload on both
      `aaa-gpt-6-luna` and `aaa-gpt-5.4-mini`. Luna may reuse the immutable
      NC-584 N-T0 record (cite it by merge commit). The missing mini
      combination needs one live request: minimal non-sensitive prompt,
      finite output-token cap, finite timeout, no automatic retries. Record
      deployment, HTTP status and reasoning-token count only (an absent count
      is "unavailable", not zero); no content, no credentials.
      **Owner authorization: granted 2026-11-19** — operator: "azure
      endpoints can be used for testing as needed."
- [x] AC-11: A `changelog/unreleased/` fragment has `type: fix`,
      `scope: providers`, and names FR-1170 / REQ-YG-732 (or the recorded
      replacement IDs).
- [x] AC-12: Git history has a genuinely failing RED behavioural test commit
      before the GREEN implementation commit; this FR records implementation
      status, decisions, evidence and deviations.

## Alternatives Considered

<a id="alternatives-considered"></a>

| # | Alternative | Probe / evidence | Disposition |
|---|-------------|------------------|-------------|
| A1 | Per-candidate `reasoning_effort:` (or free `extra:` kwargs) on race candidates | Candidates carry only `provider`/`model` (`race_node.py` `create_llm(...)` call). A new field would be a second reasoning knob next to `thinking_budget`, and FR-1056 A1 rejected that for the same reason | **Rejected.** `thinking_budget: 0` already expresses "off". Revisit if a graph needs per-candidate effort tuning. |
| A2 | Gate the mapping on model-family prefixes (`gpt-5`, `gpt-6`, `o*`) | Azure deployment names are free-form; the CSAP names are `aaa-gpt-5.4-mini` and `aaa-gpt-6-luna`, so prefixes on the deployment name are unreliable | **Rejected.** Guessing from names is a plausible wrong answer; a loud 400 from an unsupported deployment is safer. |
| A3 | Use `extra_body={"reasoning_effort": "none"}` | Offline probe: `ChatOpenAI.reasoning_effort` is a first-class field and is emitted verbatim | **Rejected.** The workaround isn't needed. |
| A4 | Drop `temperature` for Azure reasoning models (FR-455 style) | Fixes the 400 but leaves thinking on, which keeps the latency cost (1.26–1.98 ×) and discards the determinism pin that CSAP classification nodes need | **Rejected.** Treats the symptom, not the cause. |
| A5 | Do nothing and use only non-reasoning Azure models | The 400 and the latency in the Problem section stay, and `thinking_budget: 0` remains silently inert on Azure | **Rejected.** |

## Related

- `yamlgraph/utils/llm_providers.py`: `_create_azure_llm`,
  `_THINKING_PROVIDERS`, `dispatch_provider`
- `yamlgraph/utils/llm_factory.py`: `THINKING_PROVIDERS`, the `>= 1024` guard
- `yamlgraph/node_factory/race_node.py`: candidate construction passes
  `thinking_budget` from the node or graph defaults
- CSAP NC-584 evidence: `feature-requests/evidence/NC-584-luna-probe.md`
  (sections 7–9) in `terveystalo/customer-service-agent-platform`

## Out of Scope

- Effort tuning (`low`/`medium`/`high`) on Azure; see A1.
- The CSAP-side change (yamlgraph version bump and race candidate list). It
  belongs to its own CSAP FR after this ships.
- The `openai` provider (direct OpenAI) has the same gap. It is unused by the
  first consumer; the same mapping can follow in its own FR if needed.

## Judgement (2026-11-19)

**Verdict:** APPROVED WITH REVISIONS — see
[FR-1170-azure-thinking-off.judgement.md](FR-1170-azure-thinking-off.judgement.md).

R-1 (FR-1144 Azure dispatch witness superseded, in Prior art and AC-06),
R-2 (inherited-default remedies in Behaviour change, AC-05 and AC-09; the
`llm_factory.py` "no executable behaviour change" wording), and R-3 (bounded,
owner-authorized live witness in AC-10) are folded in above. Owner decision
C-6 answered: authorized. Frozen deliverables D-1 … D-6 and gates C-1 … C-7
are binding; the not-authorized list stands.

## Implementation Status

**Enforced 2026-11-19.** RED `d7ae3014` (5 failing witnesses, `KeyError:
'reasoning_effort'` and the FR-1144 call mismatch) precedes GREEN.

| Deliverable | Landed as |
|---|---|
| D-1 | `yamlgraph/utils/llm_providers.py`: `azure` added to the dispatch-side `_THINKING_PROVIDERS`; `_create_azure_llm` gained `thinking_budget`; `reasoning_effort="none"` only for `0`, other non-`None` values DEBUG-logged and dropped |
| D-2 | `tests/unit/test_fr1170_azure_thinking.py` (9 tests); `tests/unit/test_race_node.py` FR-1144 witness renamed `test_vertex_and_azure_factories_both_get_zero`, Azure factory now expects `0`, REQ-YG-724 kept |
| D-3 | `create_llm` docstring only; both `thinking_budget` rows in `reference/graph-yaml.md`, including the inherited-zero override |
| D-4 | `capabilities/CAP-307-azure-non-thinking.yaml` (REQ-YG-732, no ID collision); `ARCHITECTURE.md` regenerated |
| D-5 | `changelog/unreleased/fr-1170-azure-thinking-off.md` (`type: fix`, `scope: providers`) |

### Decisions

- **Two test layers, because CI does not install the `azure` extra.**
  `TestAzureThinkingKwargs` swaps in a fake `langchain_azure_ai` module and
  asserts the constructor kwargs (AC-01..AC-04), so the mapping is witnessed
  in CI. The real-SDK payload tests (AC-01, AC-02, AC-05 race path, AC-06
  cache) use `pytest.importorskip("langchain_azure_ai")` and run wherever the
  extra is installed (locally: 1.2.9, all pass). In CI the race composition is
  covered by its two halves: the renamed FR-1144 witness (race → factory
  receives `0`) and the kwargs layer (factory `0` → `reasoning_effort`).
  Adding `azure` to the CI extras is left as a separate proposal.
- **CAP-307 landed in the RED commit.** The `req-coverage-strict` hook rejects
  an undefined REQ, so the capability record had to precede the witnesses.

### AC-10 live evidence (2026-11-19, CSAP TEST Azure account)

Owner-authorized. Each request went through the GREEN `_create_azure_llm`
with `max_retries=0`, `timeout=30`, `max_tokens=32` and a one-line
non-sensitive prompt. No content or credentials recorded.

| Deployment | Served model | `temperature` | `reasoning_effort` | HTTP | Reasoning tokens |
|---|---|---|---|---|---|
| `aaa-gpt-5.4-mini` | `gpt-5.4-mini-2026-03-17` | 0.0 | `none` | 200 | 0 |
| `aaa-gpt-6-luna` | `gpt-6-luna-2026-09-22` | 0.0 | `none` | 200 | 0 |
| `aaa-gpt-6-luna` (contrast: budget omitted) | — | 0.0 | absent | 400 `temperature` unsupported | — |

Luna was probed fresh, so the NC-584 N-T0 record was not needed. The contrast
row reproduces the Problem section's failure through the same code path.

### Deviations

None from the frozen scope.
