# Recorded is not read

**Date:** 2026-09-24
**Arc:** `innovation_matrix` dogfood run → defect census →
[issues-2026-09-24.md](../issues-2026-09-24.md)

## What happened

The run exited 0. Two outputs were wrong: the domain never reached state, and 4
of 25 cells were lost. Each failure was written down three times — an `[ERROR]`
log line, an entry in `state.errors`, an `_error` item in the map output. Every
writer did its job. No reader existed at the two places where a reader matters:
the map fan-in, where failures become data, and the process exit, where the run
reports to its caller.

The synthesis gives no hint. It cites cells by number, reads as balanced, and
never mentions missing inputs. The loss was visible only in the raw log; the
dropped domain only when the generated dimensions were read against the brief.

## The trap

`composition_bug` in its quietest form: a write-only channel. Each component
records the error assuming someone downstream checks. The census found that
assumption false in all 202 graphs (none reads `state.errors`). The one family
that does check — the census reconcilers — re-implements the check per graph,
after the fan-in.

The same shape sits in the enforcement surface: the FR-027 safety demo for
fan-out control lints clean and does not compile. The lint verdict is recorded;
nothing reads it against a compiler.

My own version: in the first pass I wrote the timeouts down as a provider trait
("haiku timed out on long outputs"). The retry lines sat exactly 30.0 s after
each attempt start. That is the framework's own FR-708 bound on a non-streaming
call, not the provider. I attributed to the external system what was our own
boundary configuration.

## Heuristic

For every error channel, name its reader and the moment it reads. A channel with
no reader at a boundary is a log, not a control — `who_reads_this_when` applies
to failures, not only to artifacts. And when a timeout fires at a suspiciously
round number, look for our own bound before blaming the provider.

**Seed:** What if every map had to account for each dispatched index —
delivered, failed, or truncated — before any consumer ran, and `graph run`
printed that ledger as the thing its exit code reads?
