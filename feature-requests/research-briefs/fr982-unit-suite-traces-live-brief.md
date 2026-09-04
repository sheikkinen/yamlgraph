# Problem brief: the unit suite runs with the operator's LangSmith tracer live, and one FR-960 test fails when it does

**Prior art:** FR-960
(`feature-requests/FR-960-claude-judge-variant.md`, Implemented
2026-09-04, PR #577) introduced the failing test
(`tests/unit/test_fr960_claude_judge_variant.py::TestGraphRouting::test_claude_backend_visits_only_judge_claude_with_four_tools`);
its argv contract (four tools, no `Bash`/`Edit`, `--max-turns 40`) is
the value the test protects and is not in question here. FR-112
(`feature-requests/FR-112-*`, 2026-03-06, commit `4e6a1b00`) added the
`_POLLUTING_ENV_VARS = ("LANGCHAIN_TRACING",)` guard in
`tests/conftest.py` for the v1 tracing variable only. FR-432
(`feature-requests/FR-432-dotenv-upward-search.md`, Implemented) owns
the `load_dotenv` call in `yamlgraph/config.py:42-44` and its upward
search to the git boundary; that mechanism is inherited, not
reopened. FR-720 (`tests/unit/test_fr720_span_closure.py`, REQ-YG-547)
is the one existing test that deliberately sets and unsets
`LANGSMITH_TRACING`/`LANGCHAIN_TRACING_V2` via `monkeypatch`; any
change must leave that capability intact. FR-139 concerns `GIT_*` env
pollution from the enforce graph into worktree cleanup and is out of
bounds. A REJECTED-FR sweep for `LANGSMITH_TRACING`, `env pollution`,
`load_dotenv` and `conftest` found no prior proposal.

## Problem statement

`yamlgraph/config.py` calls `load_dotenv(_DOTENV_PATH)` at import time.
On any developer machine whose `.env` sets `LANGSMITH_TRACING=true`,
importing `yamlgraph` inside pytest therefore enables the LangChain
tracer for every graph the unit suite compiles and invokes.
`tests/conftest.py` strips `LANGCHAIN_TRACING` (the v1 variable) after
each test and nothing else; `LANGSMITH_TRACING` passes through
untouched. CI has no `.env` and never sets the variable, so CI and a
developer machine run two different suites.

Two consequences were measured on 2026-09-04 against clean `main`
(`6f360e55`, and earlier `ba1a009e`):

1. **The suite posts to the operator's LangSmith project.** A
   `Client.list_runs(project_name=<LANGSMITH_PROJECT>, is_root=True)`
   query over the preceding 90 minutes returned the API page maximum
   (100 root runs), dominated by `LangGraph` (89) and including runs
   named `boom_tool`, `fail_tool`, `search`, `lookup` — test-fixture
   names — and two runs whose inputs are the FR-960 test stubs verbatim:
   `{'artifact_path': 'tmp/b.md', 'backend': 'claude', 'fr_path':
   'feature-requests/X.md'}` at `06:39:44Z` and its `copilot` twin
   100 ms earlier. The unit suite is a production trace emitter on
   every developer machine with a populated `.env`.

2. **One test fails locally and passes in CI.** The FR-960 routing test
   patches `subprocess.run` globally with an ordered three-element
   `side_effect` (`claude --version`, `claude auth status`,
   `claude -p …`). With the tracer live, `LangChainTracer.on_chain_start`
   → `langchain_core.env.get_runtime_environment()` →
   `platform.platform()` → `subprocess.check_output(["file", "-b",
   <python>])` and `["uname", "-p"]` consume the list first. Traced
   argv sequence for one invoke: `uname -p`, then `file -b` ×6, then the
   three `claude` calls, then `file -b` ×2 — ten `subprocess.run` calls
   against three stubs. `claude --version` receives the JSON envelope
   stub and `_check_version` raises `unsupported Claude Code version
   '{"is_error": false, …}'`. `get_runtime_environment` is
   `@lru_cache(maxsize=1)` but never warms inside the test, because the
   stub's `stdout` is `str` and `platform.architecture` calls
   `.decode()` on it — the tracer logs `'str' object has no attribute
   'decode'` on every chain start and end, and the exception keeps the
   cache empty. Controlled runs: `LANGSMITH_TRACING=false` → 1 passed;
   tracing from `.env` → 1 failed, in isolation and with the three
   sibling `TestGraphRouting` tests preceding it.

The test's stated seam is "the Claude CLI is invoked with exactly these
arguments"; its actual seam is "the process makes exactly three
`subprocess.run` calls in this order", which couples it to whatever
else in the process shells out — including an observability layer the
test does not know is on.

## Classification

enforcement/latency-critical — a deterministic test-process boundary
(environment normalization at session start, mock seam placement) with
no LLM in the path.

## Constraints

- The FR-960 argv contract assertions (four tools, `--allowedTools`
  equality, `--max-turns 40`, no `--dangerously-skip-permissions`, no
  `Bash`/`Edit`/`mcp__*` tokens, no `copilot` call) must survive
  unchanged; only how the test intercepts the CLI may change.
- No production code path in `yamlgraph/node_factory/copilot_runtime_claude.py`
  or `copilot_node.py` may acquire a test-only flag, injection hook, or
  environment switch to make the test pass (Purge; Commandment 8).
- Tests that deliberately exercise tracing state (FR-720 AC-05,
  REQ-YG-547) must still be able to set and unset
  `LANGSMITH_TRACING`/`LANGCHAIN_TRACING_V2` via `monkeypatch` and see
  the effect.
- `yamlgraph/config.py` `load_dotenv` at import and its FR-432 upward
  search are inherited; the fix operates at the test-process boundary,
  not the library boundary.
- Local and CI unit runs must execute the same suite: whatever CI's
  tracing state is, a developer machine with a populated `.env` must
  reproduce it without manual env overrides in the command line.
- Any claim must be witnessed by a test that does not reach LangSmith
  or the Claude CLI.

## Witnessed incidents

- 2026-09-04, this repository, clean `origin/main` at `ba1a009e` in a
  detached worktree, then again at `6f360e55`:
  `pytest tests/unit/test_fr960_claude_judge_variant.py -p no:randomly`
  → `1 failed, 11 passed`. Same command prefixed with
  `LANGSMITH_TRACING=false` → passes. CI for PR #577 (which introduced
  the test) and PR #582 (which ran after it) were both green: the test
  has never been executed with the tracer on outside developer
  machines.
- 2026-09-04, same session: `traceback.extract_stack()` inside a
  `subprocess.run` stub located the extra callers at
  `langchain_core/tracers/langchain.py:330 _persist_run_single` →
  `langchain_core/env.py:19 get_runtime_environment` →
  `platform.py:1287 platform` → `platform.py:722 architecture` →
  `platform.py:671 _syscmd_file`, and `platform.py:860 processor` for
  `uname -p`.
- 2026-09-04, same session: LangSmith project query returned two root
  runs carrying the unit test's stub inputs, timestamped to the second
  the local suite ran (`06:39:44Z`); `.env` on the machine sets
  `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`,
  `LANGSMITH_ENDPOINT` (values not reproduced).
- 2026-03-06, FR-112 (`4e6a1b00`): the conftest guard was written for
  `LANGCHAIN_TRACING` because a third-party `load_dotenv` raised
  `RuntimeError` in `langchain_core ≥0.3`; the v2 variable that
  actually enables the tracer was not in scope then and has not been
  added since.
