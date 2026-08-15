# FR-798 Investigation Report — Full-Suite Failure Classification

**Status:** complete
**Git SHA:** `fd9cd8fc0fcf46f8c218654799efa4254aef54e3`
**Environments:**
- Local: Python 3.14.6, `.venv` (langgraph 1.2.9, langchain-core 1.5.1, pytest 9.1.1, pytest-xdist 3.8.0, execnet 2.1.2)
- Constrained (FR-761): Python 3.12.11, `.venv312` built from `constraints/dev-py312.txt` with `pip install -c constraints/dev-py312.txt -e ".[dev,digest,websearch,a2a,fsm,verify]"` — build exit 0, no setup blocker (`logs/fr798-venv312.log`)

Scope per judgement: the four non-subgraph classes from the FR-796 validation
run. FR-797's subgraph interrupt failures are excluded (fixed separately at
`fd9cd8fc`; not used as evidence here).

---

## Class A — RunPod `importlib.reload(config)` module identity (xdist)

### Symptom

`tests/unit/test_runpod_provider.py::TestRunpodProvider::test_default_model_reads_env_without_fallback`
fails intermittently under the pre-commit xdist run with
`ImportError: module yamlgraph.config not in sys.modules`, passes serially.

### Reproduction counts

- **Serial ×10** (`pytest <test> -q --no-cov`, repeated 10×): **10/10 passed**
  (`logs/fr798-classA-serial10.log`)
- **xdist ×20** (full pre-commit config: `pytest tests/unit/ -q --no-cov -m "not slow" -n auto`, repeated 20×):
  **19/20 passed; run 20 reproduced the failure** — `FAILED ...test_default_model_reads_env_without_fallback`
  plus the paired teardown `ERROR` (the `restore_config` fixture's own
  `importlib.reload` also raises), the exact signature of the deterministic
  witness below (`logs/fr798-classA-xdist20.log`). ~5% per-run probability,
  0% serial — consistent with the scheduling-dependent mechanism.
- **Deterministic 2-module witness (serial, both Python versions):**

  ```bash
  pytest tests/unit/test_fr432_dotenv_upward_search.py \
    "tests/unit/test_runpod_provider.py::TestRunpodProvider::test_default_model_reads_env_without_fallback" \
    -q --no-cov -p no:randomly
  # → ImportError: module yamlgraph.config not in sys.modules
  # 1 failed, 6 passed, 1 error — identical on 3.14.6 and 3.12.11
  ```

  (`logs/fr798-classA-witness2.log`, `logs/fr798-py312-classA.log`)

### Causal chain (proven, hypothesis confirmed — AC-04)

1. `tests/unit/test_fr432_dotenv_upward_search.py:20` — autouse fixture
   `_restore_config_module_state` teardown runs
   `sys.modules.pop("yamlgraph.config", None)` **without re-importing**.
2. The `yamlgraph` package object still holds its `config` attribute pointing
   at the now-orphaned module object.
3. The runpod `restore_config` fixture does `from yamlgraph import config` —
   Python returns the package **attribute** (the orphan), because attribute
   lookup precedes submodule import for already-set attributes.
4. `importlib.reload(config)` checks `sys.modules.get("yamlgraph.config") is
   config` → False → `ImportError`.

Serial full-suite runs stay green because sibling runpod tests
(`test_runpod_provider_is_registered` et al.) execute first in the same
process and their `from yamlgraph.config import ...` re-imports the module
into `sys.modules`, healing the orphan. Under xdist, per-worker test
distribution can schedule `test_fr432_dotenv_upward_search.py` on the same
worker as the runpod module without an intervening healing import — the
failure probability is a scheduling artifact, which is why it is
intermittent. `test_fr413...shared_bridge_red.py:59` pops only its own bridge
modules, not `yamlgraph.config` — ruled out.

Retries/serialization not proposed (per FR constraint); the defect is a test
isolation bug in fr432's fixture, not in the runpod test or runtime.

### Disposition (AC-10)

**Test correction** (one line, own follow-up commit outside FR-798 authority):
fr432's teardown must restore module identity — replace the bare pop with
pop + `importlib.import_module("yamlgraph.config")` (or reload the existing
module instead of popping). The 2-module witness command above is the
regression check.

---

## Class B — Memory-demo stale mock target

### Symptom

`tests/integration/test_memory_demo.py::TestMemoryDemoEndToEnd::test_tool_results_stored_in_state`
fails deterministically:
`AttributeError: <module 'yamlgraph.tools.agent'> does not have the attribute 'execute_shell_tool'`
— reproduced on 3.14.6 (`logs/fr798-check.log`) and 3.12.11
(`logs/fr798-py312-classB.log`), 2/2 runs.

### Causal chain

- The test (line 267) patches `yamlgraph.tools.agent.execute_shell_tool`.
- FR-660 (`085f3aad`, 2026-07-03, "unify tool bind/execute paths") removed
  that symbol from `agent.py`. The production call chain is now:
  `create_agent_node()` → `build_langchain_tool()`
  (`yamlgraph/tools/tool_builders.py:19,46`) → `execute_shell_tool()`
  (`yamlgraph/tools/shell.py:91`).
- The test is **stale**, the production seam moved cleanly — no dead
  re-export exists and none should be restored.

### Proposed owning seam (proven working — AC-05)

Patching `yamlgraph.tools.tool_builders.execute_shell_tool` (the module that
looks the name up at call time) makes the identical test body pass —
verified experimentally with the full agent loop executing and
`_tool_results` populated (`logs/fr798-classB-seam.log`).

### Disposition (AC-10)

**Test correction**: change the patch target string to
`yamlgraph.tools.tool_builders.execute_shell_tool`. One line; no production
change; no re-export shim.

---

## Class C — Multi-turn streaming empty response/intent

### Symptom

3 tests in `tests/integration/test_multi_turn_streaming.py` fail with empty
`response`/`intent`. Both graphs (`examples/demos/multi-turn/graph.yaml`,
`guard.yaml`) hard-code `defaults.provider: openai`.

### Full per-turn state capture (AC-07, `logs/fr798-classC-turnstate.log`)

Exhausted-key environment (the observed one):

| Surface | Turn 1 | Turn 2 (resume) |
|---|---|---|
| `__interrupt__` | present (expected) | present |
| `response` | — | `None` |
| `intent` | — | `None` |
| `errors` | `[]` | 1 × `PipelineError(type=llm_error, node=respond, retryable=true, exception_type=RateLimitError, HTTP 429 insufficient_quota/credit_balance_exhausted)` |
| checkpoint `next` | — | `('wait_for_user',)` |
| checkpoint values | — | errors persisted, no response |

Absent-key run (`OPENAI_API_KEY=""`, `logs/fr798-classCD-absentkey2.log`):
run completes, `errors` carries `unknown_error: Missing credentials...`,
same shape.

### Classification

**Provider exceptions are correctly surfaced, not silently converted to
success-shaped state**: the node's `on_error` path appends a typed
`PipelineError` to `errors`, the graph legally continues to the next
interrupt, and the checkpoint is healthy (`next=('wait_for_user',)`).
Checkpoint semantics are **independent of and unaffected by** the LLM
failure. The tests fail only because they assert the empty destination field
(`response`) and never read `errors` — the failure is **provider
unavailability**, not a product or checkpoint defect.

Secondary finding: `env -u OPENAI_API_KEY` does **not** produce an
absent-key run — `yamlgraph.config`'s `load_dotenv()` resurrects the key
from the developer's `.env` (`logs/fr798-classCD-absentkey.log` still shows
429). Any future readiness gate or provider-disabled test lane must
neutralize dotenv or use an empty-string override.

No graph or prompt artifact was edited (authoring-route boundary respected).

### Disposition (AC-10)

**Fold into the Class D follow-up**: these tests are live-provider tests
missing a readiness precondition. Once readiness gating exists (Class D),
they are expected green under a healthy credential; no separate defect. A
secondary improvement for the follow-up: the assertions should surface
`result["errors"]` in the failure message so provider failure is legible at
the assert site.

---

## Class D — Provider readiness (key presence ≠ readiness)

### Evidence (`logs/fr798-classD-ready.log`, redacted per AC-13)

| State | Probe | Outcome |
|---|---|---|
| Absent key | `OPENAI_API_KEY=""` graph run | `unknown_error: Missing credentials...` in `errors` |
| Present-but-exhausted | `create_llm(provider="openai").invoke(...)` | `RateLimitError` HTTP 429, `insufficient_quota` / `credit_balance_exhausted` |
| Healthy (operator-selected contrast) | `create_llm(provider="anthropic").invoke(...)` | `'ok'` returned |

**Readiness blocker (AC-08):** no healthy OpenAI credential is available in
this environment — the configured key has zero remaining credits (HTTP 429,
`insufficient_quota`). Successful-readiness for OpenAI specifically is
therefore blocked on operations (recharge/replace the key); the healthy
state is evidenced via the operator's Anthropic credential to prove the
probe distinguishes all three states. No credentials were created, rotated,
or pasted. Error bodies retained only as class/status/provider; account and
request identifiers omitted.

### Disposition (AC-10)

Two-part:
1. **Environment/operations action**: restore or replace the OpenAI credit
   (operator decision) — recorded blocker, no repo change.
2. **Proposed follow-up FR** (first consumer: the next enforcer running
   `tests/integration/` with any unhealthy live credential; boundary:
   provider): a documented **readiness preflight** for live-provider
   integration tests — one cheap probe per provider per session, skip with
   an explicit `provider not ready: <class/status>` reason *before*
   execution begins (satisfying the FR's rule against post-hoc error-to-skip
   conversion), dotenv-aware per the Class C secondary finding. Preflight vs
   CI credential lane vs operator selection: preflight recommended — it is
   the only option that also fixes local runs.

---

## Python 3.12 constrained-environment matrix (AC-09)

| Class | 3.14.6 local | 3.12.11 constrained |
|---|---|---|
| A (2-module witness) | ImportError reproduced | ImportError reproduced (identical) |
| B (stale mock) | AttributeError reproduced | AttributeError reproduced (identical) |
| C/D (provider) | 429 exhausted | not re-run — failure is provider-side (HTTP 429 from api.openai.com), Python-version-independent by construction; environment recorded |

Classes A and B are **not** environment artifacts. The Python 3.14 vs 3.12
difference plays no role in any of the four classes.

## Recommended enforcement order (AC-14, causal dependency)

1. **Class B test correction** — deterministic, zero dependencies, one line.
2. **Class A fixture correction** — removes the only nondeterministic red in
   the default unit lane; restores trust in the pre-commit xdist gate that
   every later step relies on.
3. **Class D readiness preflight FR** — prerequisite for interpreting any
   live-provider red; includes the dotenv-neutralization requirement.
4. **Class C re-validation** — no code change expected; re-run the three
   multi-turn tests under a healthy credential once D's gate exists. Only if
   they stay red under a ready provider does a product FR open.

Failure-count ordering would have put Class C (3 tests) first; causally it
is last because its red is downstream of D.
