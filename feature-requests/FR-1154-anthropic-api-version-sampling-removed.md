# Feature Request: FR-1154 Omit Sampling Parameters When the Anthropic API Version Removed Them

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced — [judgement](FR-1154-anthropic-api-version-sampling-removed.judgement.md) APPROVED WITH REVISIONS (R-1..R-3 folded); RED `0e9f2129`, GREEN on `fix/fr-1154-anthropic-api-sampling`
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

In `create_llm()`, after the FR-071 override and before the FR-1146 guard
(R-1: one Anthropic-only read, bound once, reused in the log):

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

Revised by judgement (R-2, R-3):

- [ ] AC-01: With `_anthropic_api_version()` returning `2026-10-21`, every FR-1146 accepting prefix and `claude-haiku-5-5` produce request payloads with no `temperature` key at the top level or in `extra_body`.
- [ ] AC-02: With `_anthropic_api_version()` returning `2027-01-01`, `claude-haiku-4-5` also omits temperature (`>=`, not equality).
- [ ] AC-03: At `2026-10-21`, `thinking_budget=1024` retains the enabled thinking payload and omits temperature; exactly one INFO record names `2026-10-21`, and no "Temperature overridden" warning is emitted.
- [ ] AC-04: With `_anthropic_api_version()` returning `2023-06-01`, the existing FR-1146 assertions and model matrix retain their behavior (accepting prefixes keep temperature, rejecting models omit it, FR-071 thinking keeps `temperature=1`); the class has deterministic old-version setup.
- [ ] AC-05: Without patching, `_anthropic_api_version()` equals `anthropic.Anthropic(api_key=...).default_headers["anthropic-version"]`; repeated calls construct/read the SDK client once per process.
- [ ] AC-06: If the SDK default headers lack `anthropic-version`, `_anthropic_api_version()` raises `KeyError`; no fallback.
- [ ] AC-07: Non-Anthropic providers do not call `_anthropic_api_version()`, preserve current temperature behavior, and the FR-455 tests remain unchanged.
- [ ] AC-08: A recorded scratch-venv run on `anthropic==2.3.0` and `langchain-anthropic==1.7.7` shows `claude-haiku-4-5` payloads without temperature both normally and with `thinking_budget=1024`; the latter retains the enabled thinking field. The FR records the command, versions, and payloads.
- [ ] AC-09: Every new test carries `@pytest.mark.req("REQ-YG-010")`; failing witnesses precede production implementation in git history.
- [ ] AC-10: `.venv/bin/python -m pytest tests/unit/test_llm_factory.py -q --no-cov`, `.venv/bin/python -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto`, and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-11: `changelog/unreleased/fr-1154-anthropic-api-version-sampling-removed.md` has `type: fix`, `scope: llm`, `req: REQ-YG-010`.
- [ ] AC-12: The FR records the folded judgement revisions and, after enforcement, the scratch witness, implementation status, decisions, and deviations.

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

Enforced 2026-10-30.

- D-1: `yamlgraph/utils/llm_factory.py` adds `ANTHROPIC_SAMPLING_REMOVED_API_VERSION`,
  the cached `_anthropic_api_version()` reader, and the version-first branch
  exactly as in the R-1 shape.
- D-2: `tests/unit/test_llm_factory.py` adds `TestAnthropicApiVersionSamplingRemoved`
  and `TestAnthropicApiVersionReader` (AC-01..AC-07). A module-level autouse
  fixture pins `2023-06-01`, so the FR-1146 class and every other Anthropic
  test are deterministic regardless of the installed SDK (AC-04). The existing
  assertions are unchanged.
- RED `0e9f2129`: 7 failed for the right reason (temperature on the wire,
  forced `1.0` with the "Temperature overridden" warning), 3 errors because
  `_anthropic_api_version` was missing, and 64 passed. The `claude-haiku-5-5`,
  old-version and non-Anthropic witnesses were already green; they are the
  regression floor.
- GREEN: `tests/unit/test_llm_factory.py` gives 74 passed.
  `req_coverage.py --strict` passes.
- AC-10, after review round 2: the exact command
  `.venv/bin/python -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto`,
  run with no venv activated and `python3` resolving to
  `/opt/homebrew/bin/python3`, gives `7675 passed, 47 skipped, 1 xfailed`.

### AC-08 SDK-2 witness (scratch venv, worktree build installed)

Exact command, run from the repository root at the PR head with
`ANTHROPIC_API_KEY` set (re-run 2026-10-30 after review P1):

```bash
set -euo pipefail
VENV=/tmp/fr1154-sdk2
rm -rf "$VENV"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install -q "anthropic==2.3.0" "langchain-anthropic==1.7.7" .
cd /tmp
"$VENV/bin/python" - <<'EOF'
import importlib.metadata as md
import yamlgraph.utils.llm_factory as f
from yamlgraph.utils.llm_factory import create_llm

print("anthropic", md.version("anthropic"), "langchain-anthropic", md.version("langchain-anthropic"),
      "header", f._anthropic_api_version())
for kw in ({}, {"thinking_budget": 1024, "max_tokens": 4096}):
    llm = create_llm(provider="anthropic", model="claude-haiku-4-5", temperature=0.7, **kw)
    p = llm._get_request_payload("hi")
    print(kw, "top-level temperature:", "temperature" in p, "extra_body:", p.get("extra_body"),
          "thinking:", p.get("thinking"))
    r = llm.invoke("Reply with the single word: ok")
    print("  live:", repr(r.text if isinstance(r.text, str) else r.text())[:60])
EOF
```

Output:

```text
[INFO] yamlgraph.utils.llm_factory: Omitting temperature: Anthropic API 2026-10-21 removed sampling parameters
[INFO] yamlgraph.utils.llm_factory: Creating LLM: anthropic/claude-haiku-4-5 (temp=None)
[INFO] httpx2: HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
[INFO] yamlgraph.utils.llm_factory: Omitting temperature: Anthropic API 2026-10-21 removed sampling parameters
[INFO] yamlgraph.utils.llm_factory: Creating LLM: anthropic/claude-haiku-4-5 (temp=None)
[INFO] httpx2: HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
anthropic 2.3.0 langchain-anthropic 1.7.7 header 2026-10-21
{} top-level temperature: False extra_body: None thinking: None
  live: 'ok'
{'thinking_budget': 1024, 'max_tokens': 4096} top-level temperature: False extra_body: None thinking: {'type': 'enabled', 'budget_tokens': 1024}
  live: 'ok'
```

The same model and SDK pair without the fix is the deviant-daily CI 400
(Probe 2, cell `2026-10-21 × claude-haiku-4-5 × 0.7`).

### Decisions and deviations

- No deviation from the folded solution in `llm_factory.py`.
- Scope deviation (review round 2, P1): AC-10's exact command was red on
  `test_ramp_installer.py::test_wrapper_delegates`. The test ran
  `scripts/ramp.sh`, which runs `exec python3`, and it inherited whatever `python3`
  came first on PATH. Without an activated venv that was homebrew, which has no
  PyYAML. The test now puts `Path(sys.executable).parent` first on the
  subprocess PATH, following the precedent in `test_req_audit_runner.py` and
  `test_issue_delegate_bundle.py`. This changes only the test; `ramp.sh` is
  unchanged. The change is out of the judged scope but required by GATE C-5.
  The test was RED under the mandated command at `33c9083c` and is GREEN after
  this change. `test_race_node.py::TestRaceNodeFactory::test_concurrent_execution`
  failed once on timing in the reviewer's run and passed in both of my full
  runs. It is not changed here.
- CI (run 41039786824, both 3.11 and 3.14) installs anthropic 2.x. Three
  Anthropic tests outside `test_llm_factory.py` then saw header `2026-10-21`
  and failed because they assert a temperature:
  `test_fr1148_thinking_off_payload`, `test_llm_factory_async::test_creates_llm`
  and `test_thinking_budget::test_thinking_budget_forces_temperature_one`.
  The `2023-06-01` pin was module-local; it now lives in `tests/unit/conftest.py`
  and covers every unit test. Locally, under SDK 2.3.0, the four affected
  modules were RED with 3 failed and are GREEN with 130 passed.
- The consumer-side move of deviant-daily to `claude-haiku-5-5` is done in
  that repository under its own governance, not under this FR (C-6).
