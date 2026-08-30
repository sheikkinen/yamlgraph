# Feature Request: Skip and Investigate `test_bare_repo_recap_no_hallucinated_conventions` (283s Single Test)

**Priority:** MEDIUM (downgraded from HIGH 2026-08-30 — the 283s premise did not reproduce)
**Type:** Bug
**Status:** Closed 2026-08-30 — investigation complete, **skip NOT applied**; premise not reproducible, disposition (d) signed off by operator; test kept unskipped with gray-zone status recorded ([judgement](FR-922-recap-bare-repo-test-skip-and-latency-investigation.judgement.md))
**Effort:** 0.5 days (investigation complete)
**Requested:** 2026-08-30
**First consumer / first event:** any developer or CI lane running `pytest tests/` with `ANTHROPIC_API_KEY` set — first event is the next full-suite run, which currently spends 34% of its wall clock inside this one test.
**Research:** in-body measurement record and dispositioned alternatives table (full-suite clock run, main @ ca44832b, 2026-08-30)
**Prior art:** FR-700 created the recap demo and this test; FR-704 moved orphan detection out of the model (cheapening one assertion but not the invocation). No prior FR addresses recap graph latency; the investigation-then-fix split follows the FR-371→FR-372 precedent (investigation_before_fix).

## Summary

`tests/integration/test_recap_demo_integration.py::TestRecapOnBareRepo::test_bare_repo_recap_no_hallucinated_conventions` took **282.98s** in the 2026-08-30 clock run — 34% of the entire 826s sequential suite, 17× the next-slowest integration test. Operator directive: **skip it now** and open an **investigation task for the rationale** — why does one recap invocation on a 3-commit bare repo take ~5 minutes, and is the test's cost/value ratio defensible in any tier.

This is an investigation-first FR per `investigation_before_fix`: the skip is the
immediate mitigation; the investigation produces the causal chain; a follow-up
fix FR (if warranted) inherits the investigation's harness as its regression
suite.

## Value Statement

Returns ~5 minutes to every keyed full-suite run immediately, and replaces a
"the LLM is slow" shrug with a measured causal chain for the recap graph's
latency.

## Problem

Measured on main @ ca44832b (2026-08-30, sequential full run):

- This test: **282.98s**. Next-slowest integration test: 16.31s.
- The test builds a 3-commit temp repo, compiles `examples/demos/recap/graph.yaml`,
  and invokes it once against Anthropic. Nothing in the test body explains
  a ~5-minute wall time for that workload.
- Unknowns (the investigation's subject): number of LLM calls the recap graph
  actually makes for a 3-commit repo; model and `max_tokens` configured;
  retries/timeouts consumed silently (`on_error: retry`?); whether prompt
  assembly scans beyond the temp repo; whether the 283s is stable or was a
  one-off degraded-API sample (single witness so far — are_the_witnesses_one_phenomenon).

The guarded behavior (REQ-YG-531: no hallucinated FR references on a
conventions-free repo) is real and worth keeping — the cost is the defect,
not the assertion.

## Proposed Solution

Two stages, both in this FR's scope:

**Stage 1 — Skip (immediate mitigation):**

```python
@pytest.mark.skip(
    reason="FR-922: 283s single-test wall time under investigation; "
    "REQ-YG-531 coverage suspended pending rationale"
)
```

Applied to the one test method. The skip reason must cite this FR so the
suspended REQ coverage is traceable, and `scripts/req_coverage.py` output for
REQ-YG-531 must be checked and its status recorded in this FR.

**Stage 2 — Investigation (the rationale):**

Deliverable is a causal chain, not a fix. Instrument one invocation of the
recap graph against the same 3-commit fixture and answer:

1. How many LLM calls, with what model, token counts, and per-call latency?
   (LangSmith trace or `YAMLGRAPH_ROUTE_LOG` + executor logging; cite trace IDs
   per Commandment 9.)
2. Is time spent in the model, in retries, or in the graph runtime?
3. Is 283s reproducible (≥3 samples) or was the clock run a degraded sample?
4. Disposition: (a) fix graph/prompt config and un-skip; (b) re-tier the test
   behind an explicit opt-in env gate with the cost documented; or (c) replace
   with a cheaper witness (e.g. haiku-class model, or record/replay) that still
   proves REQ-YG-531. The disposition is recorded in this FR and, if (a) or (c),
   spawns the follow-up fix FR.

## Acceptance Criteria

- [ ] Skip applied with FR-922-citing reason; full keyed suite no longer executes the test
- [ ] REQ-YG-531 coverage status after skip recorded in this FR (`scripts/req_coverage.py`)
- [ ] Investigation record: per-call LLM breakdown (count, model, tokens, latency) with cited LangSmith trace IDs
- [ ] Reproducibility verdict from ≥3 timed invocations
- [ ] Explicit disposition (fix / re-tier / replace witness) with rationale written into this FR
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Delete the test | Rejected — it is the only REQ-YG-531 test that executes the graph (`app.invoke`); the other 11 assert YAML shape, and none can reach the anti-hallucination clause. The assertion is sound |
| Mark `slow` only (already is) | Insufficient — `slow` does not exclude it from the full/CI keyed runs where the 283s lands |
| Fix immediately without investigation | Rejected — no causal chain yet; symptom_patch. `investigation_before_fix` applies: >15 min to even write the condemning test |
| Cheaper model swap now | Premature — may be the outcome of Stage 2 disposition (c), but choosing it before measuring is quick_confidence |

## Related

- `tests/integration/test_recap_demo_integration.py` (lines 63–92)
- `examples/demos/recap/graph.yaml`
- FR-700 (recap demo origin), FR-704 (code-owned orphan detection)
- REQ-YG-531
- FR-923 (suite latency umbrella)

## Investigation Record (2026-08-30) — completed

### Scope corrections folded from the judgement

- **R-1 (two-channel coverage):** `scripts/req_coverage.py` extracts
  `@pytest.mark.req(...)` statically from the AST, so a `@pytest.mark.skip`
  would leave REQ-YG-531 reported as covered while the live witness stopped
  running. Static status today: `REQ-YG-531 (12 tests)`. Runtime status is a
  separate channel and must be reported from pytest skip output, never from
  the registry.
- **R-2 (targeted verification):** verification uses the single-node-id command,
  not a full keyed suite rerun.
- **R-3 (evidence contract):** LangSmith was available; trace IDs are cited per
  sample below. No Commandment-9 compliance is claimed beyond what the cited
  traces show.
- **R-4 (out of scope):** this FR authorizes no CI lane, coverage-core, pytest
  default, model, prompt, or recap graph change.

### Reproducibility verdict: **NOT reproducible — the 283s was a single outlier**

| Sample | Condition | Wall | LangSmith run | Tokens (prompt/completion) |
|---|---|---|---|---|
| Original (FR premise) | full suite, sequential, coverage ON | 282.98s | not captured | — |
| 1 | test alone, no coverage | 46.59s | `01a05268-1362-7062-a51c-656be530b06a` | 499 / 1206 |
| 2 | test alone, no coverage | 41.44s | `01a05268-d10b-7bd1-bd5e-f63431e979d4` | — / — (1229 total) |
| 3 | test alone, no coverage | 12.95s | `01a05269-7ebe-7901-ab67-d2868fc61379` | — / — (1576 total) |
| 4 | full `tests/integration/` lane, no coverage | 78.35s | — | — |

Four controlled witnesses span 12.95s–78.35s. The 283s never recurred. Per
`are_the_witnesses_one_phenomenon`, the original single sample cannot carry a
skip decision on its own.

### Causal chain: the graph runtime is innocent

Child-run breakdown of sample 1 (`langsmith_traces.py children`):

| Node | Type | Latency |
|---|---|---|
| `get_commits` | shell | 0.07s |
| `get_churn` | shell | 0.05s |
| `get_frs` | shell | 0.04s |
| `get_fragments` | shell | 0.04s |
| `get_fr_statuses` | shell | 0.05s |
| `partition` | python | 0.00s |
| **`synthesize`** | **llm** | **44.66s** |
| `finalize_recap` | python | 0.00s |

One LLM call, `claude-haiku-4-5` (`yamlgraph/config.py:67` default; the prompt
sets no model, `max_tokens`, or `thinking_budget`). Deterministic nodes total
0.25s — **99.4% of wall time is the single Anthropic call**, and no retry or
loop occurred (`_loop_counts` all 1, `errors: []`).

Two observations the trace makes visible:

1. **Completion length is disproportionate.** 499 prompt tokens produce 1206
   completion tokens for a final answer of two workstream strings and an empty
   hotspot list — roughly 40 tokens of signal. The remainder is model verbosity
   inside structured output. This is `read_raw_output_first` territory and the
   only genuine latency lever inside our control.
2. **Latency scales with surrounding load, not with input.** Identical input
   costs 12.95s alone and 78.35s inside the integration lane. The original
   283s was measured under the full suite *with coverage instrumentation on*,
   which FR-923 independently measured at +107% overhead.

### Disposition: (d) do NOT skip — close without suspending the witness

The FR's stated operator directive was "skip it now", predicated on a 283s
cost. That cost is not the test's steady-state behaviour.

REQ-YG-531 carries 12 tests, but they are not interchangeable. Eleven live in
`tests/unit/test_recap_demo.py`; nine of those are `yaml.safe_load` plus an
assertion on the parsed dict (node counts, `git -C` present, `@{` absent,
`-n 300` present, schema fields, edge pairs), and the remaining two exercise a
single tool node and a git subprocess. **None calls `app.invoke`.** The
integration test is the only one that compiles and runs the graph, and
therefore the only witness for the clause no YAML parse can reach: that the
model invents no `FR-\d+` references on a repo that has none.

Applying the skip would leave 11 structural tests and zero executing ones,
while `req_coverage.py` — which extracts `@pytest.mark.req` statically from the
AST — continued to report `REQ-YG-531 (12 tests)`. A `gate_checks_shape_not_substance`
outcome: paying real coverage for an imaginary saving.

The residual cost is already owned elsewhere: FR-923's integration lane runs
**without coverage**, which removes the largest measured multiplier from this
test's worst observed case. No new FR is spawned.

### Operator verdict (2026-08-30): gray zone, kept unskipped

Disposition (d) signed off. The operator's assessment on review: the test sits
in a **gray zone** on three axes, and the latency I measured is only the first.

1. **Time.** 12.95s–78.35s steady-state, 283s at its worst observed. Even the
   floor is an order of magnitude above every other REQ-YG-531 test.
2. **Unorthodox YAMLGraph usage.** The test asserts a vendor its graph never
   declares — see the provider-binding finding below.
3. **Poor fit in the testing pipeline in the first place.** What it validates
   is a *demo's output quality under a live model*. That is an evaluation
   concern, not a regression gate: non-deterministic, priced per run, and its
   failure mode (a model inventing an `FR-\d+`) is a prompt regression rather
   than a code regression. It was filed as an integration test because that
   was the available shape, not because it is one.

Kept unskipped for now — removing the only executing REQ-YG-531 witness would
trade a measured cost for an unmeasured gap. Recorded as a candidate for
relocation to an evaluation lane rather than permanent residence in the
regression suite; that relocation is out of scope here and belongs with
FR-923's lane work.

### Finding: silent provider binding (gray-zone axis 2)

The `synthesize` node in `examples/demos/recap/graph.yaml` declares neither
`provider` nor `model`:

```yaml
  synthesize:
    type: llm
    prompt: recap
```

The prompt YAML declares neither either. The node resolves to the global
default (`claude-haiku-4-5`, `yamlgraph/config.py`), and the test hardcodes
that unstated resolution in its skip condition:

```python
pytestmark = pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), ...)
```

A provider-agnostic artifact gated on one vendor's key. Under `PROVIDER=openai`
the test skips on a missing Anthropic key while the graph it exercises would
have run fine. The same coupling appears in five integration files
(`test_recap_demo_integration`, `test_fr713_pending_census`,
`test_thinking_budget_integration`, `test_fr725_harness`,
`test_race_loser_teardown`).

This bears directly on the latency result: the 44.66s and the ~1206 completion
tokens carrying ~40 tokens of signal both belong to a model **nobody chose**.
An unpinned LLM node is an unmade decision that is also unreadable.

**Why nothing flagged it.** The "no direct LLM calls" rule is enforced by
`scripts/lint_inline_llm.py` (FR-047, pre-commit hook `inline-llm-check`),
which fires only when a file has `def main(` **and** imports an LLM symbol
**and** does not import a graph loader. The `def main(` precondition makes the
entire `tests/` tree invisible to it, and `examples/demos/` is excluded
wholesale by `EXCLUDE_PATHS`. The rule inspects the *import list* — a static
shape — while the vendor is decided by *runtime default resolution*. No
import-shaped check can see an unstated default: `gate_checks_shape_not_substance`
at the enforcement layer.

The recap test is **not** itself a direct-call violation — it imports
`load_and_compile`, and the call reaches Anthropic through `execute_prompt` →
`create_llm()`. The gap is the binding, not the call.

**Follow-up (own FR, not spawned here):** drop the `def main(` precondition
from `lint_inline_llm.py` with a confession-backed allowlist for legitimate
`ChatAnthropic` type-assertions; add a graph-lint rule requiring committed
example `llm` nodes to pin `provider` and `model` or opt out explicitly.

### Incidental finding (out of scope, needs its own FR)

`tests/integration/test_race_loser_teardown.py::test_race_loser_teardown_live`
passes alone (19.32s) and fails inside the integration lane:

```
AssertionError: race 3: thread growth 9 -> 10: [... 'Thread-1 (tracing_control_thread_func)',
'Thread-2 (tracing_control_thread_func_compress_parallel)', ...]
assert 10 <= 9
```

The growth is LangSmith's own `tracing_control_thread_func` workers, which
spawn lazily once tracing is active — the test's baseline snapshot includes
threads owned by a different subsystem, so the assertion is order-dependent.
This is test pollution, not a race-teardown defect. Not fixed here; it belongs
to a separate FR.

### Evidence logs

`logs/fr922-sample-{1,2,3}.log`, `logs/fr922-integration-suite.log`,
`logs/fr922-detail.log`, `logs/fr922-children.log`, `logs/fr922-req531.log`,
`logs/fr922-race-isolated.log`.
