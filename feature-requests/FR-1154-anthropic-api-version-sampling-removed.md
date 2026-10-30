# Feature Request: FR-1154 Omit Sampling Parameters When the Anthropic API Version Removed Them

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Requested:** 2026-10-30
**First consumer / first event:** `sheikkinen/deviant-daily` daily publish.
Its `describe` node (`create_llm(provider="anthropic")` →
`claude-haiku-4-5`) has failed every scheduled run since 2026-10-28 with
`Error code: 400 - invalid_request_error 'temperature: Extra inputs are not permitted'`
(GitHub Actions runs 40698055110, 40885030950, 41025372292).
**Research:** in-body [Alternatives Considered](#alternatives-considered)
table, each row backed by a probe executed 2026-10-30 (FR-889 style).
**Prior art:** [FR-1146-anthropic-temperature-deprecated.md](FR-1146-anthropic-temperature-deprecated.md)
— per-*model* omission (allowlist of five 4.x lines that accept
temperature). This FR does not replace that rule; it adds the axis FR-1146
could not see: the per-*API-version* removal. Under API `2026-10-21` the
allowlisted lines reject temperature too;
[FR-455-reasoning-model-temperature-guard.md](FR-455-reasoning-model-temperature-guard.md)
— OpenAI branch, untouched;
[FR-071-thinking-budget-graph-level.md](FR-071-thinking-budget-graph-level.md)
— forces `temperature=1` under extended thinking; under API `2026-10-21`
the forced `1` is itself a 400 (Probe 2), so this FR must also stop sending it.

## Summary

The `anthropic` Python SDK 2.0.0 (2026-10-21) sends
`anthropic-version: 2026-10-21`. Anthropic's versioning page says of that
version: "The `temperature`, `top_p`, and `top_k` request parameters are
removed. A request that sends any of them returns a 400 error on every
model." yamlgraph still sends `temperature` to the five FR-1146 allowlisted
lines (including the default model `claude-haiku-4-5`). With SDK 2 installed,
every LLM node on those models fails before producing a token.

## Value Statement

A fresh `pip install yamlgraph` resolves to the newest SDK. Any downstream
project that installs without a lockfile (deviant-daily does) breaks the day
upstream releases. This FR makes yamlgraph correct under either SDK major
without a pin.

## Problem

### Causal chain (probed 2026-10-30)

| Run | yamlgraph | anthropic | langchain-anthropic | Result |
|---|---|---|---|---|
| deviant-daily 2026-10-27 | 0.6.5 | 1.17.0 | 1.7.6 | OK |
| deviant-daily 2026-10-28 | 0.6.5 | **2.3.0** | **1.7.7** | 400 |

- `langchain-anthropic` 1.7.6 declared `anthropic<2.0.0,>=0.120.0`. In 1.7.7
  the dependency is `anthropic>=0.120.0`, so the cap is gone and pip picked SDK 2.3.0.
- `anthropic/_constants.py` in 2.3.0 sets `ANTHROPIC_API_VERSION = "2026-10-21"`.
  The client sends it as the `anthropic-version` default header.
  `anthropic.Anthropic(api_key="x").default_headers["anthropic-version"]`
  returns `2026-10-21` on 2.3.0 and `2023-06-01` on 0.125.0. Both values were read locally.
- In SDK 2, `Messages.create` no longer has `temperature`, `top_p` or `top_k` arguments.
  The SDK's `MIGRATION.md` routes them through `extra_body`.
  `langchain-anthropic` 1.7.7 does exactly that:
  `ChatAnthropic(model="claude-haiku-4-5", temperature=0.7)._get_request_payload(...)`
  yields `extra_body={"temperature": 0.7}`. With `temperature=None` it yields
  `extra_body=None`. Both payloads were probed in a scratch venv with 2.3.0/1.7.7.
- `create_llm()` keeps the resolved temperature for allowlisted 4.x lines
  (FR-1146). It also forces `temperature=1` under `thinking_budget >= 1024`
  (FR-071). The value reaches the wire in `extra_body`, and the server rejects it.

### Probe 2: live acceptance matrix

Raw SDK 0.125.0, `max_tokens=8`, `anthropic-version` header overridden per row:

| `anthropic-version` | model | none | `temperature=0.7` | `temperature=1` |
|---|---|---|---|---|
| 2023-06-01 | claude-haiku-4-5 | OK | OK | OK |
| 2023-06-01 | claude-haiku-5-5 | OK | 400 deprecated for this model | OK |
| 2026-10-21 | claude-haiku-4-5 | OK | **400 Extra inputs are not permitted** | **400** |
| 2026-10-21 | claude-haiku-5-5 | OK | 400 | 400 |

The `2026-10-21 × claude-haiku-4-5 × 0.7` cell gives the exact deviant-daily
CI message. Omission is accepted in every cell.

### Where the premise broke

FR-1146 says the accepting set is "closed (older generations, no new
releases expected)". That still holds per model. The removal comes from a
second axis, the API version, and it overrides the model axis completely.

## Ideal Result

yamlgraph never sends a sampling parameter that the API version on the wire
rejects. That version is the `anthropic-version` header the installed SDK
sends. The rule follows that header, not a version pin. On SDK 1.x
(`2023-06-01`), FR-1146 behaviour is byte-identical. On any header
`>= 2026-10-21`, every Anthropic request omits temperature, including the
FR-071 forced `1`. An info log names the API version.

## Planned Operations

```yaml
probes:
  - "pytest tests/unit/test_llm_factory.py before edit — FR-1146 TestAnthropicSamplingGuard is the regression floor; it runs on the pinned SDK (constraints/dev-py312.txt anthropic==0.120.0 → header 2023-06-01)"
  - "scratch venv with anthropic 2.3.0 + langchain-anthropic 1.7.7 + this worktree installed: create_llm payload has no temperature in extra_body for claude-haiku-4-5, with and without thinking_budget"
  - "live call through create_llm on SDK 2.x for claude-haiku-4-5 returns a message (if the scratch venv reaches the network; else record the payload witness and deviant-daily CI as the live witness after release)"
branches:
  - "SDK exposes no anthropic-version in default_headers → refuse loudly (KeyError surfaces), do not guess a version"
  - "header < 2026-10-21 → FR-1146 path unchanged"
delegations:
  - "judge.sh: 1 run"
  - "review.sh: 1 run after PR"
waits:
  - "judge"
  - "CI"
commands:
  - scripts/judge.sh feature-requests/FR-1154-anthropic-api-version-sampling-removed.md
  - .venv/bin/python -m pytest tests/unit/test_llm_factory.py -q --no-cov
  - .venv/bin/python -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto
  - python scripts/req_coverage.py --strict
  - scripts/review.sh
```

## Proposed Solution

In `yamlgraph/utils/llm_factory.py`:

```python
# First Anthropic API version that rejects temperature/top_p/top_k on every model (FR-1154)
ANTHROPIC_SAMPLING_REMOVED_API_VERSION = "2026-10-21"


@functools.cache
def _anthropic_api_version() -> str:
    import anthropic

    return anthropic.Anthropic(api_key="unused").default_headers["anthropic-version"]
```

In `create_llm()`, after the FR-071 override and before the FR-1146 guard:

```python
if (
    selected_provider == "anthropic"
    and _anthropic_api_version() >= ANTHROPIC_SAMPLING_REMOVED_API_VERSION
):
    logger.info(f"Omitting temperature: Anthropic API {version} removed sampling parameters")
    temperature = None
    temperature_overridden = False
elif <FR-1146 guard, unchanged>:
    ...
```

Constraints:

1. The version source is the installed SDK's own default header, read once
   per process. No network call is made, and nothing private is imported.
   The header is ISO `YYYY-MM-DD`, so string comparison orders it.
2. `temperature_overridden = False` keeps the FR-071 warning ("overridden to
   1.0") from claiming a value that was never sent.
3. The cache key already uses the post-guard temperature. All temperatures
   on SDK 2 share one client per model, which matches the single wire request.
4. `anthropic` is a core dependency (`pyproject.toml`), so the import cannot be missing.
5. No pin is added to `pyproject.toml`.

## Acceptance Criteria

- [ ] AC-01: With `_anthropic_api_version()` returning `2026-10-21`,
  `create_llm(provider="anthropic", model="claude-haiku-4-5", temperature=0.7)`
  builds a client whose request payload carries no temperature, neither top-level
  nor in `extra_body`. This holds for every FR-1146 allowlisted prefix and for `claude-haiku-5-5`.
- [ ] AC-02: Same version with `thinking_budget=1024` builds a payload with no
  temperature. The `thinking` field is still enabled with that budget. No
  "Temperature overridden" warning is logged.
- [ ] AC-03: The omission logs one INFO record naming the API version.
- [ ] AC-04: With `_anthropic_api_version()` returning `2023-06-01`, all
  existing FR-1146 tests pass unchanged. The FR-1146 test class pins the
  version explicitly, so it does not depend on the SDK that happens to be installed.
- [ ] AC-05: Without patching, `_anthropic_api_version()` equals the installed
  SDK's `anthropic.Anthropic(api_key=...).default_headers["anthropic-version"]`.
- [ ] AC-06: Non-Anthropic providers are unaffected, and the FR-455 tests are unchanged.
- [ ] AC-07: Scratch-venv witness on anthropic 2.3.0 / langchain-anthropic
  1.7.7: the `create_llm` payload for `claude-haiku-4-5` has `extra_body`
  without temperature. The output is recorded in this FR.
- [ ] AC-08: New tests carry `@pytest.mark.req("REQ-YG-010")`, and the RED commit precedes GREEN.
- [ ] AC-09: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` and
  `python scripts/req_coverage.py --strict` pass.
- [ ] AC-10: `changelog/unreleased/fr-1154-anthropic-api-version-sampling-removed.md`
  exists with `type: fix`, `scope: llm`, `req: REQ-YG-010`.
- [ ] AC-11: This FR records implementation status and deviations.

## Out of Scope

- Moving deviant-daily to `claude-haiku-5-5` is a consumer change in that
  repo. It cures the outage on its own, because 5.5 is outside the FR-1146
  allowlist and already omits temperature. It does not cure the 4.x lines or
  the thinking-forced `1`, which is why this FR exists.
- `top_p`/`top_k`: yamlgraph never sends them (grep `top_p|top_k` in
  `yamlgraph/utils/`: no senders).

## Alternatives Considered

**is_this_a_graph:** no. This is a deterministic constructor rule at the
provider boundary.

| # | Alternative | Probe / evidence | Disposition |
|---|---|---|---|
| A | Pin `anthropic<2` in `pyproject.toml` | yamlgraph's `pyproject.toml` declares `anthropic>=0.96.0` and `langchain-anthropic>=1.5.1`, both uncapped. A cap keeps the old contract alive and blocks every SDK 2 feature for all users. | Rejected: a doctrine-forbidden preservation of an old contract; it postpones the break instead of removing it |
| B | Send temperature via `extra_body` (MIGRATION.md's route) | This is already what langchain-anthropic 1.7.7 does, and Probe 2 row 3 gives 400 | Rejected: measured failing |
| C | Force header `anthropic-version: 2023-06-01` on SDK 2 | It would override the SDK's own contract and send SDK-2-shaped requests to an old API version | Rejected: version skew; it only defers the break |
| D | Key on `anthropic.__version__` major ≥ 2 | Correlated with the header today, but the vendor statement is about the API version, not the SDK major | Rejected: keys on a proxy when the real value (the header) is one attribute away |
| E | **Key on the installed SDK's `anthropic-version` header** (chosen) | Header read locally on both SDKs; vendor doc names this version as the removal point | Chosen: it normalizes at the boundary with the exact value the wire carries |

## Related

FR-1146, FR-455, FR-071, FR-1148, FR-1151.

## Implementation Status

Not started.
