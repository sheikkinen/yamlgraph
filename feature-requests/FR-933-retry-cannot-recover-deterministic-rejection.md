# FR-933: Retry Cannot Recover a Deterministic Schema Rejection

**Priority:** HIGH
**Type:** Defect
**Status:** Implemented 2026-08-31 — RED `e8e7c83d`, GREEN `5078a0a9`
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

FR-938 enforcement. Its AC-10 (a live `scripts/research.sh` run) could not be
satisfied: five consecutive runs failed, across two briefs and four distinct
persona/field combinations, every one on `String should have at most 400
characters`. A counterfactual run at pre-FR-938 code failed the same way, so the
route is red independently of that FR — but red is red, and it belongs to
whoever finds it.

## Traces

| run | brief | persona | field |
|---|---|---|---|
| 1 | fr-938-prior-art-precedent | os_infra_primitivist | rationale |
| 2 | fr-938-prior-art-precedent | os_infra_primitivist | rationale |
| 3 | fr-938-prior-art-precedent | os_infra_primitivist | rationale |
| 4 | fr-929-local-diary-existence | librarian_structure | rationale |
| 5 (pre-FR-938 code) | fr-929-local-diary-existence | yamlgraph_native_planner | candidate |

Run 5 is the counterfactual: `examples/demos/research-route/{graph.yaml,nodes/research_tools.py}`
checked out at `13feeeac`, which is the unmodified pre-FR-938 state.

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
  feature-requests/research-briefs/fr-938-prior-art-precedent-brief.md`
  exits 0, writes a non-empty `tmp/draft-alternatives.md` containing five
  persona rows, that artifact passes
  `python scripts/research_preflight.py tmp/draft-alternatives.md` with
  zero violations, and a matching provenance line whose `brief_path` is
  that brief is appended to `feature-requests/research-runs.jsonl`. This is
  the evidence FR-938 AC-10 could not produce.
- **AC-10** New tests carry `@pytest.mark.req(...)`; a changelog fragment
  exists in `changelog/unreleased/`; this FR gains an implementation-status
  section; a diary reflection is added.

## Out of scope

Changing `max_length=400`; truncating, coercing, or otherwise editing
invalid model output; weakening any Pydantic schema; changing the persona
prompts or `examples/demos/research-route/graph.yaml`; adding a new
`on_error` mode; reviving FR-408's `auto_repair`, code registry,
`inject-default`, or threshold relaxation; changing the judge, research, or
authoring invocation routes; anything in the FR-938 frozen scope.

## Implementation status (2026-08-31) — Implemented

RED `e8e7c83d` (`tests/unit/test_fr933_validation_feedback_retry.py`, five
tests: two condemning, three regression guards), GREEN `5078a0a9`. Every
acceptance criterion holds; no condition of the judgement was waived beyond
C-6, whose waiver is recorded at the head of this document.

### What was built

`yamlgraph/node_factory/validation_feedback.py` (new) turns a
`ValidationError` into one bounded diagnostic string: the failing field path
(`err["loc"]`), the sanitized message, the constraint metadata Pydantic
exposes in `err["ctx"]`, and `len(err["input"])` rendered as "you sent N".
The rejected value itself is never carried — `_sanitize` redacts it, and
`str(ValidationError)` is never rendered, because Pydantic embeds the input
in its own repr (AC-03, AC-08).

`llm_execution._feedback_aware_attempt` is a stateful closure over the
attempt callable: it holds the last validation error and passes the derived
feedback to the next attempt, logging `Retry carrying validation feedback:
%s`. `error_handlers.handle_retry` was deliberately left untouched — its
zero-argument callable contract is what the non-validation witnesses in
AC-06/AC-07 depend on, and threading feedback through the closure instead of
the handler is what keeps them passing unmodified.

### Deviation D-3 — the executor was touched

The approved D-3 file list named only `error_handlers.py`,
`llm_execution.py`, and `llm_nodes.py`. But the approved FR *text* specifies
feedback "appended by the executor as a correction instruction", and nothing
in the node layer can reach the message list. Transport was therefore added:
`PromptRequest.retry_feedback: str | None = None`, a matching
`execute_prompt(..., retry_feedback=None)` parameter, and one
`messages.append(HumanMessage(...))` in `PromptExecutor.execute`. This is the
sanctioned extension point — FR-715's docstring on `PromptRequest` reads "Add
a parameter HERE; the witnesses force the mirrors to follow", and the mirrors
did follow. The deviation is recorded in the GREEN commit message and here;
it widens the file list, not the behaviour.

### The measurement defect that invalidated the first live evidence

AC-01's premise — that retries were byte-identical — was *asserted* from
reading the code before it was ever *observed*, and the first attempts to
observe it failed in a way that nearly sent the investigation into the code
under test. After the fix was in the worktree, live runs still showed zero
feedback log lines. An unconditional probe log placed in the changed function
also never fired. Root cause: `scripts/research.sh` resolves its executor via
`command -v yamlgraph`, which is a **console script**. Console scripts do not
put the working directory on `sys.path`, so every "live" run of this branch
was importing the framework from the **main checkout** — measuring code that
did not contain the fix. Proven directly:

```
sys.path.pop(0) → package: /Users/sheikki/.../yamlgraph/yamlgraph/__init__.py
                  has helper: False
```

With `PYTHONPATH="$PWD"` the run exits 0, the feedback log fires twice, and
the retry converges. The probe has since been removed. Consequence: **no live
evidence from this branch is valid unless the invocation pins the
interpreter.** This is Scripture's `artifact_carries_code_identity` firing in
real time, and the same defect class recurs in `scripts/ramp.sh` and
`.github/hooks/scripts/checks/yaml-checks.sh`; the route repair is filed
separately rather than smuggled in here.

### AC-09 live witness

`scripts/research.sh` on the FR-938 brief exits 0; `tmp/draft-alternatives.md`
carries five persona rows and passes `scripts/research_preflight.py` with zero
violations; the provenance line is appended to
`feature-requests/research-runs.jsonl` with the brief path and the code SHA.
The same run also produced FR-938's first real prior-art block — the two
defects were blocking each other, and neither was visible until the other
moved.
