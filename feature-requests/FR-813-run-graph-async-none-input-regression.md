# Feature Request: run_graph_async crashes on None initial_state (LangGraph checkpoint re-run) since FR-811

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced 2026-08-17
**Effort:** 0.5 days
**Requested:** 2026-08-17
**First consumer / first event:** ninchat_voice (csap) NC-434 — the moment it
bumps to 0.5.21 and a node-recovery retry fires: its retry path calls
`run_graph_async(app, None, config)` to re-run only the failed node from the
checkpoint, which now raises `TypeError` before `ainvoke`.

**Prior art:** FR-811 / CAP-212 / REQ-YG-570 is the governing OTel runner
boundary and introduced this regression. NC-434 is the first-consumer contract
that exposed the missing input shape. No separate runner or checkpoint feature
is proposed; this FR restores the existing LangGraph `ainvoke(None, config)`
path within FR-811's frozen span schema.

## Summary

FR-811 (v0.5.21) moved `run_graph_async` into `observability/otel.py` and
added unconditional input normalization:

```python
variables = (
    initial_state if isinstance(initial_state, dict) else asdict(initial_state)
)
```

(`yamlgraph/observability/otel.py:300-302`). `None` is a valid LangGraph
input meaning "resume from checkpoint state" — the pre-FR-811 runner passed
it through to `ainvoke` untouched. Now `asdict(None)` raises
`TypeError: asdict() should be called on dataclass instances` **before**
`app.ainvoke`, and it does so **even when `YAMLGRAPH_OTEL_EXPORT` is unset**,
because the normalization is outside the OTel-enabled guard. This violates
FR-811's own AC-06 ("with the switch unset, `run_graph_async` … retains its
current return, interrupt, route-log, and exception behavior") — a behavior
regression for every embedded host using checkpoint re-runs.

Reproduced 2026-08-17 on v0.5.21:

```python
await run_graph_async(app, None, {"configurable": {"thread_id": "t1"}})
# TypeError: asdict() should be called on dataclass instances
```

The focused runtime witness also proves `app.ainvoke` is never reached:

```text
TypeError: asdict() should be called on dataclass instances
ainvoke_calls=0
```

Source history identifies `ce0189c0` (`feat(observability): FR-811 export
programmatic run spans`) as the introducing commit. The same witness against
the pre-FR-811 implementation passes `None` directly to `app.ainvoke`.

## Value Statement

Embedded hosts using LangGraph's checkpoint re-run contract
(`ainvoke(None, config)` — e.g. ninchat_voice's failed-node retry, which
re-runs ONLY the failed node without double-executing prior nodes) can adopt
0.5.21+ without their recovery path crashing.

## Problem

The signature says `initial_state: dict[str, Any] | Command`, but the de
facto pre-FR-811 contract accepted anything `ainvoke` accepts, including
`None`. NC-434's cross-check flagged `None` as the untested input shape in
FR-811's AC-04; the release confirmed it as a crash, not a hash question.

## Ideal Result

`run_graph_async(app, None, config)` behaves exactly as before FR-811 when
OTel is disabled, and when OTel is enabled it exports a root span with a
deterministic hash for the None-input case (hash of canonical `null`),
leaking no raw values — per the existing `variables_hash` contract which
already handles `None` (`json.dumps(None)` → `"null"`).

## Proposed Solution

Normalize `None` explicitly before the dataclass branch:

```python
variables = (
  initial_state
  if initial_state is None or isinstance(initial_state, dict)
  else asdict(initial_state)
)
```

`None` is not normalized to `{}`: those are different LangGraph inputs and
different evidence identities. Widen `run_graph_async.initial_state` to
`dict[str, Any] | Command | None`. Widen the hashing-input annotations on
`graph_run_span` and `variables_hash` only as needed to admit `None`; do not
change their runtime serialization or other public behavior. Pass
`initial_state` through to `ainvoke` unchanged.

The frozen evidence representation is canonical JSON `null`, whose SHA-256 is
`74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`.
Canonical `{}` is explicitly forbidden for this path; its distinct hash is
`44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.

## Acceptance Criteria

- [x] AC-01: `run_graph_async(app, None, config)` with OTel disabled returns
      `ainvoke`'s result; no OpenTelemetry import, no exception — RED test
      first (condemns v0.5.21 behavior).
- [x] AC-02: Same call with OTel enabled and an in-memory exporter emits one
  root span whose `yamlgraph.variables.hash` equals the SHA-256 of canonical
  JSON `null`
  (`74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b`),
  and exports no raw values. The hash of `{}` is not accepted.
- [x] AC-03: dict and `Command` inputs unchanged (existing FR-811 tests
      stay green).
- [x] AC-04: `run_graph_async`, `graph_run_span`, and `variables_hash` type
  annotations admit the `None` hashing path without weakening unrelated
  public contracts; the runner docstring documents `None` as checkpoint
  re-run input.
- [x] AC-05: Tests are marked with existing REQ-YG-570; CAP-212 remains the
  governing capability and strict requirement coverage passes.
- [x] AC-06: Changelog fragment and diary entry are included.

## Alternatives Considered

- **Host-side workaround (csap passes `{}` instead of `None`):** changes
  LangGraph semantics — `{}` is a new input, `None` means resume-from-
  checkpoint; not equivalent, rejected.
- **Guard normalization behind `is_otel_enabled()` only:** fixes the
  disabled-path regression but leaves the enabled-path crash; both must be
  fixed.
- **Hash `None` as `{}`:** conflates checkpoint continuation with an empty new
  input and produces a different evidence hash; rejected.

## Related

- FR-811 / REQ-YG-570 / CAP-212 — introduced the regression in v0.5.21
  (`yamlgraph/observability/otel.py:300-302`)
- ninchat_voice NC-434 — first consumer; its AC-04 predicted this input
  shape ("verify this input shape when bumping to the FR-811 release")
- ninchat_voice `actions/real/_yamlgraph_async_retry.py:60` — the calling
  site (`run_graph_async(app, None, config)` re-runs only the failed node)

## Decisions (2026-08-17)

- Preserve `None` through both evidence hashing and `app.ainvoke`; never
  substitute `{}`.
- Canonical JSON `null` is the frozen OTel evidence representation.
- Extend existing REQ-YG-570 / CAP-212 tests; create no new capability or
  requirement.
- Scope is limited to the `None` checkpoint re-run regression. Direct compiled
  invocation, native streaming, span schema, route grammar, and exporter
  configuration remain unchanged.

## Judgement (2026-08-17)

**Verdict:** APPROVED — authority is active within the scope frozen in
`FR-813-run-graph-async-none-input-regression.judgement.md`.

### Questions for the human (as options, or 'none')

None.

## Implementation Status (enforced 2026-08-17)

All acceptance criteria are complete. `run_graph_async` now admits `None` in
its public annotation, preserves it unchanged for LangGraph checkpoint
continuation, and hashes it through the existing canonical JSON path. The
evidence hash is the frozen SHA-256 of `null`, remains distinct from the hash
of `{}`, and exposes no raw input value. `graph_run_span` and `variables_hash`
admit the same evidence shape without changing exporter or span behavior.

Validation evidence:

- RED commit `eeafeb34`: both direct witnesses failed at `asdict(None)` before
  `ainvoke`, reproducing the v0.5.21 regression.
- Focused FR-813 witnesses: 2 passed.
- Complete OTel and async executor suites: 51 passed.
- Route-evidence and structural module-boundary witnesses: 23 passed.
- Full fast unit suite: 5,817 passed, 97 skipped, 1 xfailed.
- Strict requirement coverage: 405/405 requirements covered.
- Ruff format/check, Radon grade-D scan, and generated FR-board check passed.
