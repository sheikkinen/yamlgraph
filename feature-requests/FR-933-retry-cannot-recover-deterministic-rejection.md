# FR-933: Retry Cannot Recover a Deterministic Schema Rejection

**Priority:** HIGH
**Type:** Defect
**Status:** Revised 2026-08-30 — awaiting rejudgement
**Judgement:** [FR-933-retry-cannot-recover-deterministic-rejection.judgement.md](FR-933-retry-cannot-recover-deterministic-rejection.judgement.md)
— REJECTED on first submission (R-1 missing research evidence; R-2 dangling
FR-926 path and undispositioned FR-408). R-1..R-5 folded below.
**Research:** [FR-933.research.md](FR-933.research.md) — **route waived by
operator 2026-08-30** under judgement condition C-6, which requires the
waiver be recorded before rejudgement. The waived record is hand-written,
not persona output, and says so; it dispositions seven alternatives and six
precedents and answers `is_this_a_graph`: no. The waiver is necessary
because `scripts/research.sh` is the artifact under repair — it cannot
produce evidence for the FR that fixes it. Precedent for the form:
`feature-requests/FR-927-retire-fr902-lane-guard-hooks.md:7`.
**Effort:** 0.5 day
**Requested:** 2026-08-30
**First consumer:** `scripts/research.sh` — the research sole route, currently
failing every run.
**Prior art:** `feature-requests/FR-896-research-route-precedent-traceability.md`
froze `max_length=400` with "rejection never truncation" and is the contract this
defect lives inside; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`
established the persona schema; `feature-requests/FR-926-research-failure-cites-recorded-cause.md`
built the error channel that made this diagnosable at all.
**`feature-requests/FR-408-runtime-repair-metadata.md` (Rejected)** is the
dispositive precedent the first draft of this FR failed to cite. It proposed
framework-side repair of values — `on_error: auto_repair`, an `RT-XXX` code
registry, `coerce-field-type`, `inject-default`, `relax-threshold` — and was
rejected as disproportionate, with two repairs judged actively harmful. FR-933
is distinguished on exactly that axis: **the framework never repairs a value.**
It adds a description of the violated constraint to the retry input and lets
the model repair its own output. Every FR-408 mechanism is forbidden below and
in the frozen out-of-scope list. Full disposition:
[FR-933.research.md](FR-933.research.md).

## Summary

`on_error: retry` re-issues a byte-identical request. At `temperature: 0.0` a
schema validation failure is therefore retried into the same failure, and
`max_retries: 2` buys nothing but latency.

## Escalated from

FR-932 enforcement. Its AC-10 (a live `scripts/research.sh` run) could not be
satisfied: five consecutive runs failed, across two briefs and four distinct
persona/field combinations, every one on `String should have at most 400
characters`. A counterfactual run at pre-FR-932 code failed the same way, so the
route is red independently of that FR — but red is red, and it belongs to
whoever finds it.

## Traces

| run | brief | persona | field |
|---|---|---|---|
| 1 | fr-932-prior-art-precedent | os_infra_primitivist | rationale |
| 2 | fr-932-prior-art-precedent | os_infra_primitivist | rationale |
| 3 | fr-932-prior-art-precedent | os_infra_primitivist | rationale |
| 4 | fr-929-local-diary-existence | librarian_structure | rationale |
| 5 (pre-FR-932 code) | fr-929-local-diary-existence | yamlgraph_native_planner | candidate |

Run 5 is the counterfactual: `examples/demos/research-route/{graph.yaml,nodes/research_tools.py}`
checked out at `13feeeac`, which is the unmodified pre-FR-932 state.

## Violated objective

CAP-248 claims a working research sole route. The route currently cannot
complete, so the capability is a phantom claim.

## Root cause

`yamlgraph/node_factory/llm_execution.py`:

```python
if cfg.on_error == ErrorHandler.RETRY:
    nr = handle_retry(
        node_name,
        lambda: attempt_execute(cfg.provider),   # identical request
        cfg.max_retries,
    )
```

The retry closure captures no attempt index and varies no input. Retry is a
correct strategy for *transient* faults — timeouts, 429s, connection resets —
and a no-op for *deterministic* ones. A structured-output schema rejection at
temperature 0 is deterministic by construction. The graph declares
`on_error: retry, max_retries: 2` on all five persona nodes and receives three
identical failures.

The prompts are not the lever. Every field in
`examples/demos/research-route/prompts/*.yaml` already states "hard cap 400
characters; over-length output is rejected, never truncated", and there is a
`BREVITY IS MECHANICALLY ENFORCED` block. This is `two_strike_split` at its
fifth strike: the level is mechanizable, so it belongs in code.

## Proposed constraint

**One mechanism, frozen (R-3): bounded validation feedback on retry.**

When a node parsing structured LLM output raises a Pydantic
`ValidationError`, the next node-level retry attempt must receive feedback
derived from that failed parse. Every other exception class keeps its
current retry, fallback, skip, and fail behaviour byte-for-byte.

The feedback is bounded:

| Must include | Must not include |
|---|---|
| the failing field path | the rejected over-length value, whole or truncated |
| the validation message | any framework-authored replacement value |
| the limit and actual length, when the constraint exposes them | any change to the schema or its constraints |

The feedback is appended by the executor as a correction instruction. It is
**not** a template variable — the persona prompt YAML is not edited, which
is what keeps AC-08 and the graph-authoring boundary (R-5) intact.

The seam, for scope only — enforcement chooses the exact signature under
TDD, and the judgement's C-2 requires the RED test first:

- `handle_retry` currently takes `Callable[[], ...]` and starts with
  `last_exception = None` (`yamlgraph/error_handlers.py:108-136`), so it
  can neither pass the previous failure to the next attempt nor see the
  initial one. Both are required.
- `attempt_execute` closes over `variables` resolved once before its
  definition (`yamlgraph/node_factory/llm_nodes.py:322-350`), which is why
  the feedback cannot ride in on the existing variables dict without
  re-resolution.

### Explicitly not FR-408 (R-2)

FR-408 was rejected for framework-side repair of values. FR-933 forbids
every mechanism that earned that rejection, and the exclusions below are
binding, not aspirational: no `on_error: auto_repair` or any new `on_error`
mode; no `RT-XXX` diagnostic-code registry; no repair-handler dispatch
table on `PipelineError`; no `coerce-field-type`; no `inject-default`; no
`relax-threshold` or any threshold relaxation; no silent coercion; no
truncation. The framework never edits a value — it reports a constraint and
lets the model repair its own output inside the schema that already exists.

### Rejected alternative, recorded

**Classify `ValidationError` as non-retryable** is a correct diagnosis and
an insufficient cure: it converts a 3× wall into a 1× wall and the research
route still never completes, failing the stated first consumer. It is
merged into this FR as the *exhaustion* behaviour (AC-06), not as the
implementation path. Full disposition of this and five other candidates in
[FR-933.research.md](FR-933.research.md).

## Acceptance criteria

- **AC-01** RED: a unit test builds an LLM node with structured output,
  `on_error: retry`, `max_retries: 2`, and a stub `execute_prompt` that
  raises `ValidationError` on every attempt while recording the arguments
  it received. Before the fix, every recorded attempt is equal. The test
  asserts on the recorded *inputs*, not on the call count.
- **AC-02** GREEN: the same recorded inputs show attempt 2 carrying the
  failing field path and the validation message, and the limit and actual
  length when the constraint exposes them.
- **AC-03** The recorded retry input does **not** contain the rejected
  over-length value — asserted by searching the attempt-2 payload for a
  distinctive substring of the value rejected at attempt 1.
- **AC-04** Success path: a stub that fails validation once and succeeds on
  the second attempt yields a node result whose parsed output is stored
  under the node's `state_key`, proving feedback retry can actually
  converge rather than merely differ.
- **AC-05** Exhaustion: when every attempt fails validation, the node
  returns a `PipelineError` preserving node name, exception type, and the
  validation message. No truncated value, no coerced value, and no
  success-shaped state update is produced.
- **AC-06** Non-validation exceptions are untouched: the existing witnesses
  `tests/unit/test_reliability.py:159-207` and
  `tests/unit/test_executor_retry.py:185-219` pass unmodified, and a new
  test proves a non-`ValidationError` retry receives an input identical to
  its first attempt.
- **AC-07** Executor-level provider classification
  (`yamlgraph/executor_base.py:60-77`, `yamlgraph/executor.py:140-164`) is
  unchanged in behaviour; retryable provider faults still retry under the
  existing policy.
- **AC-08** No persona prompt, no `examples/demos/research-route/graph.yaml`,
  no `max_length=400`, and no rejection-never-truncation contract is
  changed. If enforcement finds a governed graph or prompt artifact must
  change, it stops and re-judges rather than editing — and any such change
  is produced by `scripts/author.sh` with `tmp/draft-authoring-report.md`
  recording lint, smoke, and limitations.
- **AC-09** Live witness: `scripts/research.sh
  feature-requests/research-briefs/fr-932-prior-art-precedent-brief.md`
  exits 0, writes a non-empty `tmp/draft-alternatives.md` containing five
  persona rows, that artifact passes
  `python scripts/research_preflight.py tmp/draft-alternatives.md` with
  zero violations, and a matching provenance line whose `brief_path` is
  that brief is appended to `feature-requests/research-runs.jsonl`. This is
  the evidence FR-932 AC-10 could not produce.
- **AC-10** New tests carry `@pytest.mark.req(...)`; a changelog fragment
  exists in `changelog/unreleased/`; this FR gains an implementation-status
  section; a diary reflection is added.

## Out of scope

Changing `max_length=400`; truncating, coercing, or otherwise editing
invalid model output; weakening any Pydantic schema; changing the persona
prompts or `examples/demos/research-route/graph.yaml`; adding a new
`on_error` mode; reviving FR-408's `auto_repair`, code registry,
`inject-default`, or threshold relaxation; changing the judge, research, or
authoring invocation routes; anything in the FR-932 frozen scope.
