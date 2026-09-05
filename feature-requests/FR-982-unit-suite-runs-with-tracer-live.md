# Feature Request: the unit suite must not run with the operator's LangSmith tracer live

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-09-04
**Judgement:** [FR-982-unit-suite-runs-with-tracer-live.judgement.md](FR-982-unit-suite-runs-with-tracer-live.judgement.md)
— APPROVED WITH REVISIONS (2026-09-04); graph verdict SPLIT overridden by
the operator, D-2 retained; R-2/R-3/R-4 folded below.
**First consumer / first event:** any developer running
`pytest tests/unit/test_fr960_claude_judge_variant.py` on a machine whose
`.env` sets `LANGSMITH_TRACING=true` — today that command fails on clean
`main` (`6f360e55`) while CI for the same commit is green; and, on the
same run, the operator's LangSmith project receives every graph the
suite invokes.
**Research:** in-body dispositioned alternatives table below (FR-890 R-6
equivalent record). The sole route was attempted twice on 2026-09-04
(`scripts/research.sh feature-requests/research-briefs/fr982-unit-suite-traces-live-brief.md`,
brief passed preflight); both runs failed at `librarian_research` with
all nine `search_web` calls timing out on every ddgs engine while
`curl` and `httpx` reached the same hosts (brave 200/429, ddg 202).
The route last succeeded at 05:22Z the same day, so the outage is
environmental (egress for the `primp` client), not a brief defect. The
brief is committed at
[research-briefs/fr982-unit-suite-traces-live-brief.md](research-briefs/fr982-unit-suite-traces-live-brief.md)
for re-running when egress returns.
**Prior art:** [FR-960-claude-judge-variant.md](FR-960-claude-judge-variant.md)
— introduced the failing test (PR #577); its argv contract is the value
this FR preserves, and the seam it uses is the defect this FR repairs.
[FR-140](FR-140-clean-git-env-test-fixture.md) / `CAP-41` — the session-scoped
`_clean_git_env` fixture is the exact precedent: strip environment the
test process inherits from outside, at session start, restore on
teardown; this FR adds the tracing variables to that boundary.
`tests/conftest.py:28-47` — the existing `_POLLUTING_ENV_VARS =
("LANGCHAIN_TRACING",)` guard, a per-test pop of the v1 variable only;
the v2 variable that actually enables the tracer was never covered.
Its comment claims FR-112 provenance (commit `4e6a1b00`);
[FR-112-inception-provider.md](FR-112-inception-provider.md) itself
specifies no test-environment contract, so the conftest guard is the
evidence and FR-112 is claimed provenance only (judgement R-4). [FR-432-dotenv-upward-search.md](FR-432-dotenv-upward-search.md)
— owns `load_dotenv` at import in `yamlgraph/config.py`; inherited, not
reopened. [FR-720-close-trace-spans-on-loser-cancel.md](FR-720-close-trace-spans-on-loser-cancel.md)
— its AC-05 test sets and unsets the tracing variables via
`monkeypatch`; that capability must survive. [FR-139](FR-139-enforce-worktree-bare-corruption-guard.md)
— `GIT_*` pollution in the enforce graph; dismissed, different boundary.
A REJECTED-FR sweep for `LANGSMITH_TRACING`, `env pollution`,
`load_dotenv`, `conftest` returned nothing.

## Summary

`yamlgraph.config` loads `.env` at import. On a developer machine that
sets `LANGSMITH_TRACING=true`, importing `yamlgraph` under pytest turns
the LangChain tracer on for every graph the unit suite compiles and
invokes. Two consequences: the suite posts hundreds of test-fixture
runs to the operator's LangSmith project, and one FR-960 test — which
stubs `subprocess.run` with an ordered three-element list — fails
because the tracer's `get_runtime_environment()` shells out first and
consumes the stubs. CI has no `.env`, so CI is green and local is red.
The fix is at the test-process boundary: force tracing off at session
start (the FR-140 pattern), and make the FR-960 stub dispatch on what
was called rather than on call order.

## Value Statement

Every developer gets the same unit-suite verdict CI gets, from any
machine, without command-line overrides; and the operator's LangSmith
project stops receiving `boom_tool`, `fail_tool` and stub-FR traces
from local test runs.

## Problem

Measured on 2026-09-04 against clean `origin/main` (`ba1a009e` in a
detached worktree, then `6f360e55`).

**1. The test.** `tests/unit/test_fr960_claude_judge_variant.py::TestGraphRouting::test_claude_backend_visits_only_judge_claude_with_four_tools`
does:

```python
with patch("subprocess.run",
           side_effect=[_proc(VERSION_OK), _proc(AUTH_OK), _proc(ENVELOPE_OK)]) as m:
    final = app.invoke({...,"backend": "claude", ...})
```

With the tracer live, `app.invoke` makes **ten** `subprocess.run` calls,
not three. Stack captured from inside the stub:

```
langchain_core/tracers/langchain.py:330 _persist_run_single
langchain_core/env.py:19              get_runtime_environment
platform.py:1287                      platform
platform.py:722                       architecture
platform.py:671                       _syscmd_file        → ["file", "-b", <python>]
platform.py:860                       processor           → ["uname", "-p"]
```

Observed argv order: `uname -p`, `file -b` ×6, `claude --version`,
`claude auth status`, `claude -p …`, `file -b` ×2. The first stub
(`VERSION_OK`) is eaten by `uname`; `claude --version` receives the
JSON envelope and `_check_version` raises
`unsupported Claude Code version '{"is_error": false, …}'`.

`get_runtime_environment` is `@lru_cache(maxsize=1)`, but the cache
never warms inside this test: the stub's `stdout` is a `str`, and
`platform.architecture` calls `.decode()` on it, so the tracer logs
`'str' object has no attribute 'decode'` on every chain start and end
and the exception keeps the cache empty. Hence `file -b` is re-issued
per run event.

Controlled runs on the same commit:

| condition | result |
|---|---|
| `.env` tracing on, test alone, `-p no:randomly` | 1 failed |
| `.env` tracing on, whole `TestGraphRouting` class | 1 failed, 3 passed |
| `LANGSMITH_TRACING=false` on the command line | 1 passed |
| CI for PR #577 (introduced the test) and PR #582 | green |

The test's stated seam is "the Claude CLI receives exactly these
arguments". Its actual seam is "the process makes exactly three
`subprocess.run` calls in this order" — coupled to any layer that
shells out, including an observability layer the test does not know is
on.

**2. The leak.** `Client.list_runs(project_name=<LANGSMITH_PROJECT>,
is_root=True)` over the preceding 90 minutes returned the API page
maximum, 100 root runs: `LangGraph` 89, `search` 8, `lookup` 1,
`boom_tool` 1, `fail_tool` 1 — test-fixture names — including two runs
whose inputs are the FR-960 stubs verbatim,
`{'artifact_path': 'tmp/b.md', 'backend': 'claude', 'fr_path':
'feature-requests/X.md'}` at `06:39:44.143Z` and its `copilot` twin
100 ms earlier. The unit suite is a production trace emitter on every
developer machine with a populated `.env`.

**3. The guard that exists.** `tests/conftest.py` has
`_POLLUTING_ENV_VARS = ("LANGCHAIN_TRACING",)`, popped *after* each
test. `langsmith.utils.tracing_is_enabled` resolves
`LANGSMITH_TRACING_V2` → `LANGCHAIN_TRACING_V2` → `LANGSMITH_TRACING`
→ `LANGCHAIN_TRACING` and compares to the string `"true"`; the guard
covers one of four names, and pops rather than overrides, so any later
third-party `load_dotenv` (the very case the guard's comment names)
restores it. The lookup goes through `langsmith.utils.get_env_var`,
which is `@functools.lru_cache(maxsize=100)` — the first read per
`(name, default)` is memoized for the process, so any env mutation
must be followed by `get_env_var.cache_clear()` to be observed
(verified at judgement fold, 2026-09-04).

## Ideal Result

The unit suite is hermetic with respect to observability: running it on
any machine, with any `.env`, yields the verdict CI yields and sends
nothing to LangSmith. A test that needs tracing *on* says so with
`monkeypatch` and gets it. A test that stubs a CLI intercepts that CLI
and nothing else.

## Proposed Solution

Two deliverables, both under `tests/`; no production module changes.

**D-1 — normalize tracing at the session boundary** (`tests/conftest.py`,
the `_clean_git_env` pattern):

```python
_TRACING_ENV_VARS = (
    "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING_V2",
    "LANGSMITH_TRACING", "LANGCHAIN_TRACING",
)

@pytest.fixture(autouse=True, scope="session")
def _tracing_off():
    """Force the LangChain/LangSmith tracer off for the whole session.

    yamlgraph.config loads .env at import; a developer's
    LANGSMITH_TRACING=true would otherwise trace every test graph to
    their project. Override rather than delete: python-dotenv never
    overwrites an existing key, so "false" survives any later load.
    """
    from langsmith.utils import get_env_var

    saved = {k: os.environ.get(k) for k in _TRACING_ENV_VARS}
    for k in _TRACING_ENV_VARS:
        os.environ[k] = "false"
    get_env_var.cache_clear()  # lru_cache: first read is memoized
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    get_env_var.cache_clear()
```

`_prevent_env_pollution` / `_POLLUTING_ENV_VARS` become redundant
(the session fixture covers `LANGCHAIN_TRACING` with a stronger
guarantee) and are removed.

**D-2 — dispatch the FR-960 stub on argv, not on position**
(`tests/unit/test_fr960_claude_judge_variant.py`):

```python
def _claude_cli(responses: list[MagicMock]):
    """subprocess.run stand-in: hand `responses` to `claude` calls in order;
    answer anything else (platform probes, etc.) with an empty success."""
    queue = list(responses)
    def run(argv, *a, **k):
        if argv and argv[0] == "claude":
            return queue.pop(0)
        m = MagicMock(); m.stdout, m.returncode, m.stderr = b"", 0, b""
        return m
    return run
```

The routing test uses `patch("subprocess.run", side_effect=_claude_cli([...]))`
and its existing assertions run unchanged over the `claude` calls only
(`_agent_calls` already filters). Everything else in the test file is
untouched.

## Acceptance Criteria

- [ ] AC-01: `tests/conftest.py` has a session-scoped autouse fixture
  that sets all four tracer variables (`LANGSMITH_TRACING_V2`,
  `LANGCHAIN_TRACING_V2`, `LANGSMITH_TRACING`, `LANGCHAIN_TRACING`) to
  `"false"` at session start, clears `langsmith.utils.get_env_var`'s
  cache, and restores their prior state at teardown. Override, not
  delete.
- [ ] AC-02: witness (`tests/unit/test_fr982_tracing_off_in_tests.py`):
  inside a test, `langsmith.utils.tracing_is_enabled()` is `False` and
  `langchain_core.tracers.context._tracing_v2_is_enabled()` is falsy,
  and each of the four variables reads `"false"`.
- [ ] AC-03: witness (judgement R-2): a test that does
  `monkeypatch.setenv("LANGSMITH_TRACING_V2", "true")` — the
  highest-priority alias, the only one that can override the session
  default — then `get_env_var.cache_clear()`, observes
  `tracing_is_enabled()` become `True` and
  `_tracing_v2_is_enabled()` truthy; teardown restores `"false"` and
  clears the cache again so the result is independent of test order.
  Opt-in still works (protects FR-720 AC-05 / REQ-YG-547; those tests
  stay green).
- [ ] AC-04: RED first: on `main` `6f360e55` with `.env` tracing on,
  `pytest tests/unit/test_fr960_claude_judge_variant.py -p no:randomly`
  fails (1 failed, 11 passed) with no command-line env override; after
  D-1 it passes with D-2 not yet applied. Both runs recorded in the
  Implementation Status.
- [ ] AC-05: the FR-960 routing test stubs `subprocess.run` with an
  argv-dispatching callable; every existing assertion in
  `test_claude_backend_visits_only_judge_claude_with_four_tools` is
  byte-identical.
- [ ] AC-06: witness for the seam: feeding `_claude_cli` the sequence
  `["uname","-p"]`, `["file","-b","x"]`, `["claude","--version"]`,
  `["file","-b","x"]`, `["claude","auth","status"]`, `["claude","-p","…"]`
  returns the three responses to the three `claude` calls in order and
  `returncode == 0` with `bytes` stdout for the others.
- [ ] AC-07: `_prevent_env_pollution` and `_POLLUTING_ENV_VARS` are
  removed from `tests/conftest.py` only after AC-01–AC-03 are green;
  the old guard's concern (v1 variable raising in `langchain_core ≥
  0.3`) is covered by AC-01.
- [ ] AC-08: live witness (judgement R-3), recorded in Implementation
  Status: after the fix, on a machine with `.env` tracing on, run
  `LANGSMITH_PROJECT=fr982-witness-<sha>-<utc> pytest tests/unit -q
  --no-cov -m "not slow" -n auto`; record commit SHA, exact start/end
  timestamps and the project name; after client flush/settle, query
  `Client.list_runs(project_name=<that>, is_root=True)` and record the
  result — it must be **zero root runs** (not merely none matching the
  three known signatures).
- [ ] AC-09: `git diff --stat main -- yamlgraph/` is empty (no
  production change).
- [ ] AC-10: `capabilities/CAP-261-tracing-off-in-tests.yaml` registers
  `REQ-YG-644` (`fr: FR-982`, modules `tests/conftest.py`,
  `tests/unit/test_fr982_tracing_off_in_tests.py`); `ARCHITECTURE.md`
  regenerated; AC-02/AC-03 tests carry `@pytest.mark.req("REQ-YG-644")`;
  the AC-06 seam test carries `REQ-YG-642` (CAP-211, FR-960's own
  requirement); `python scripts/req_coverage.py --strict` exits 0.
  IDs re-verified against `origin/main` at push time (cap-req race,
  recurrence #7 on 2026-09-04).
- [ ] AC-11: `fix` changelog fragment in `changelog/unreleased/` naming
  FR-982 and REQ-YG-644; diary reflection at
  `docs/diary/diary-<date>-reflection-fr-982-<slug>.md`.

## Alternatives Considered

Dispositioned in the research record's frozen column set. Every row
carries a detail produced by an executed probe, not a prior.

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Session fixture overrides the four tracer vars to `"false"` (D-1) | os_infra_primitivist | enforcement/latency-critical | ACCEPT | `_clean_git_env` (FR-140, CAP-41) | no | low / low | Probe: `LANGSMITH_TRACING=false` → 1 passed on the same commit that fails without it. `tracing_is_enabled` compares to the literal `"true"`, so `"false"` is a real off. python-dotenv never overwrites an existing key, so the override survives any later third-party `load_dotenv` — the failure mode the existing conftest guard's own comment describes. |
| Session fixture *deletes* the tracer vars | os_infra_primitivist | enforcement/latency-critical | REJECT | `tests/conftest.py` `_prevent_env_pollution` (pops) | no | low / medium | Probe: `yamlgraph/config.py:44 load_dotenv` runs at import; the conftest comment records litellm calling `load_dotenv()` again at import. A deleted key is restored by the next load (repo memory `dotenv-restores-unset-keys`, and this session's `env -u AZURE_MODEL` failure under FR-966). Delete is a race; override is not. |
| `yamlgraph.config` skips `load_dotenv` when under pytest | yamlgraph_native_planner | enforcement/latency-critical | REJECT | FR-432 owns the loader | no | low / high | Production code acquiring test awareness violates the brief constraint and Commandment 8 (no compat flags). Also changes behaviour for every FR-432 consumer, not just tests. |
| Fix only the FR-960 stub seam (D-2 alone) | subtractionist | enforcement/latency-critical | ACCEPT as complement, REJECT as sole fix | — | no | low / low | Probe: with the tracer on the graph made 10 `subprocess.run` calls; an argv dispatcher would pass. But the LangSmith query (100 root runs / 90 min, fixture names, stub inputs at `06:39:44Z`) shows the leak continues. Fixes the symptom's test, not the boundary. |
| Patch `yamlgraph.node_factory.copilot_runtime_claude.subprocess.run` instead of `subprocess.run` | data_process_planner | enforcement/latency-critical | REJECT | — | no | low / — | Probe: `copilot_runtime_claude.py:23 import subprocess` — the module attribute *is* the global `subprocess` module, so the patch target resolves to the identical function object. False locality; same ten calls intercepted. |
| Warm `langchain_core.env.get_runtime_environment()` once in conftest so the tracer never shells out | data_process_planner | enforcement/latency-critical | REJECT | — | no | low / medium | Probe: it is `@lru_cache(maxsize=1)` and warming works. But it couples the suite to a private langchain_core detail, leaves the tracer on (leak continues), and the FR-960 test would still be one un-cached subprocess away from failing. |
| Set the tracer vars in CI to match local | librarian_research | enforcement/latency-critical | REJECT | — | no | low / high | Inverts the goal: CI would start posting to LangSmith from GitHub runners with whatever key is configured. The hermetic side is the right side to converge on. |
| Point the tracer at a null `LANGSMITH_ENDPOINT` in tests | os_infra_primitivist | enforcement/latency-critical | REJECT | — | no | low / medium | Tracer still runs `get_runtime_environment` → still shells out → FR-960 still red. Adds a network-failure path (background client retries) instead of removing one. |

`is_this_a_graph`: no candidate involves an LLM judgement or a fan-out
over a corpus; this is deterministic test-process configuration.

## Related

- Brief: [research-briefs/fr982-unit-suite-traces-live-brief.md](research-briefs/fr982-unit-suite-traces-live-brief.md)
- Failing test: `tests/unit/test_fr960_claude_judge_variant.py:279`
- Boundary: `tests/conftest.py` (`_POLLUTING_ENV_VARS`, `_clean_git_env`)
- Loader: `yamlgraph/config.py:42-44`
- Tracer entry: `langchain_core/tracers/langchain.py:330`,
  `langchain_core/env.py:19`
- PR #577 (FR-960, introduced the test), PR #582 (ran green after it)
- LangSmith evidence: project `<LANGSMITH_PROJECT>` root runs
  `06:39:44.042Z` and `06:39:44.143Z` on 2026-09-04 (inputs are the
  FR-960 stubs); operator-visible in the project UI, not reproduced
  here to keep the public repo free of the project name.

## Implementation Status

**Status:** Implemented 2026-09-04 on `feat/fr982-unit-suite-traces-live`.
No production change (`git diff --stat main -- yamlgraph/` empty, AC-09).

Commit trail (C-4 RED → GREEN-D1 → GREEN-D2):

| commit | content |
|---|---|
| `500d37e3` | judgement folded (APPROVED WITH REVISIONS; SPLIT overridden) |
| `cc7cde02` | `tests/unit/test_fr982_tracing_off_in_tests.py` + `CAP-261`/REQ-YG-644 + regenerated `ARCHITECTURE.md`; 4 failed — three on absent aliases / `tracing_is_enabled()` reading the `.env` value, the seam witness on the missing `_claude_cli` helper (the helper *is* D-2) |
| `974f8f02` | D-1 `_tracing_off` session fixture; `_prevent_env_pollution` removed |
| `0a4d5472` | D-2 `_claude_cli` argv dispatcher; routing assertions byte-identical |

AC-04 record (both runs with `.env` `LANGSMITH_TRACING=true`, no
command-line override, `-p no:randomly`):

- RED on `500d37e3`: `1 failed, 11 passed in 3.08s` — `test_claude_backend_visits_only_judge_claude_with_four_tools`
  (`logs/fr982-ac04-red.log`).
- GREEN after D-1 only, D-2 not applied: FR-960 file 12/12 passed;
  FR-720 file passed; tracing witnesses passed; only the AC-06 seam
  witness still red (`20 passed, 1 failed`, `logs/fr982-ac04-green-d1.log`).

AC-08 live witness (judgement R-3), on the D-1+D-2 tree (pre-reword SHA
`e39f0770`+D-2, content-identical to `0a4d5472` — the RED commit's
message was reworded afterwards, see Decisions):

- Command: `LANGSMITH_PROJECT=fr982-witness-e39f0770-20260904T075749Z pytest tests/unit -q --no-cov -m "not slow" -n auto`
- Window: `2026-09-04T07:57:49Z` → `2026-09-04T07:59:07Z`; result
  `6655 passed, 90 skipped, 1 xfailed in 76.74s`.
- Query after a 20 s settle: `Client.list_runs(project_name=<witness>, is_root=True)`
  → `LangSmithNotFoundError: Project … not found`. LangSmith creates a
  project on its first ingested run, so the project's non-existence is
  the strongest form of "zero root runs": not one event reached the
  API. Control: the operator's default project had **0** root runs in
  the same window (`logs/fr982-ac08-query.log`).

Decisions and deviations:

- The old guard's v1 concern (`LANGCHAIN_TRACING` set ⇒ RuntimeError in
  `langchain_core ≥ 0.3`) is covered because `env_var_is_set` treats
  `"false"` as unset (`langchain_core/utils/env.py:18-21`) — verified
  before removing `_prevent_env_pollution` (AC-07).
- The D-1 GREEN commit was made with `SKIP=pytest`: the pre-commit hook
  runs the whole unit suite and the AC-06 seam witness is deliberately
  still red at that point (C-4 requires D-1 to land before D-2). The
  run it would have made is recorded above; the D-2 commit ran the full
  hook set unskipped.
- The seam witness's RED fails on `ImportError` of `_claude_cli`. AC-11
  excludes import errors as a *masking* cause; here the missing symbol
  is the deliverable itself, and the substantive RED for the seam is
  AC-04's positional-stub failure. Recorded rather than hidden.
- Under `pytest-xdist` the session fixture runs once per worker
  process, which is the correct boundary: each worker imports
  `yamlgraph.config` and loads `.env` independently.
- The RED commit was first recorded with a stale `tmp/msg.txt` (the
  fold commit's message: the `ruff check` failure in the same `&&`
  chain had prevented the new message from being written, and the
  retry reused the old file). Reworded before push via non-interactive
  rebase; D-1/D-2 SHAs changed accordingly, content did not.
