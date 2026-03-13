# Diary: NC-150 fly.io Monitoring UI — Debug Session 2026-03-12

## What we were doing

Bringing the statemachine monitoring UI live on fly.io (NC-150). The UI was already
working locally. The goal: `./monitor-fly.sh` → browser → see live state transitions
during a Twilio call.

## Traps encountered

### Trap 1: IPv4/IPv6 mismatch (WireGuard boundary)

`--host 0.0.0.0` looked correct. Port was "listening." But fly proxy routes via
WireGuard, which assigns IPv6 addresses (`fdaa::/48`). IPv4-only binds are unreachable.
The tell: `cat /proc/net/tcp` showed `0xBBA` bound, `cat /proc/net/tcp6` was empty for
that port. Node.js auto-binds dual-stack (`::`) which is why port 3001 worked but 3002
didn't. Fix: `--host ::`.

**Cure applied**: Normalize at the boundary (platform layer). `/proc/net/tcp6` is
the right diagnostic tool for WireGuard-routed ports.

### Trap 2: config_type ≠ diagram directory name (boundary: filename vs metadata)

The UI requested `/api/diagram/voice_coordinator_simple` (file stem of the YAML
passed to the engine). Diagrams were generated at `docs/fsm-diagrams/voice_coordinator/`
(`metadata.machine_name`). The mismatch was invisible — no warnings, just 404s.

`start-fsm.sh` already solved this with a runtime copy trick. We missed applying
the same pattern to the fly.io deployment. The fix was `entrypoint.sh`.

**Cure applied**: When a boundary (filename vs metadata value) produces two
identifiers, normalize at the entry point. The `start-fsm.sh` precedent was the
signal — if the local script needed the trick, the deploy did too.

### Trap 3: One-shot socket connect → silent event drop (the most subtle)

After all the above fixes, the UI loaded and showed the diagram but status never
updated. Calls worked. A classic "thing that works but gives no signal it's broken."

Root cause: `EventSocketManager._connect()` is called once at `__init__`. If the
Unix socket file doesn't exist at that moment (startup race), `self.sock = None`
forever. Every `emit()` short-circuits at `if not self.sock` and returns `False`.
The log line is at DEBUG level — invisible at INFO.

The `_connect()` retry in the `except` branch on line 83 is unreachable when
`self.sock is None`. It only fires on send failures. Classic "plausible wrong answer"
from the codebase: the code *looks* like it handles reconnection.

Verified via pid ordering: before the fix, `fsm-engine` (pid 663) started the same
second as `websocket-server` (pid 664) — a coin flip. After `priority=10` and the
poll-wait wrapper, `websocket-server` consistently gets pid 662.

**Cure applied**: Deployment-level: `priority=10` for websocket-server + poll-wait
wrapper in fsm-engine command. Library-level: filed FR in fsm/docs/ — the proper
fix is lazy reconnect in `emit()`.

## Heuristic extracted

> A log line at DEBUG that says "cannot emit" is a silent lie when you need WARNING.
> Silent drops of monitoring events are production defects, not debug noise.

This is the **audit_as_ritual** trap from the Knowledge Graph — we ran multiple
deploy cycles before finding the root cause because the symptom (frozen UI) looked
like it could come from anywhere.

**New instance of**: `plausible_wrong_answer` — the reconnect code on line 83 gave
false confidence that reconnection was handled.

## What worked well

- `/proc/net/tcp` and `/proc/net/tcp6` as diagnostic tools for bind-address issues
- `pid` ordering as the verification signal for startup sequencing
- Tracing `config_type` through `Path(config_path).stem` → diagram directory to
  find the 404 source without guessing

## Seed

If `EventSocketManager` had emitted a single WARNING per dropped event, this bug
would have been caught on the first deployment. What is the minimum observability
contract a library component should meet? "Never silently drop data" seems obvious —
but how do we enforce it systematically? Should library components that emit events
have a health-check endpoint or a counter that callers can inspect?

**FR filed**: `fsm/docs/feature-request-event-socket-lazy-reconnect.md`
