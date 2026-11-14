# FR-1165: The key whose test proved it parsed

**Date:** 2026-11-14
**FR:** FR-1165 (refuse graph-level `config.max_tokens`)

## What happened

An operator's graph set a token limit where the reference docs said to put
it, and every call ran at the provider default. Feature request 027 had
added the parse, a schema entry, a docs row, a requirement line ("wired from
YAML config/node config") and two tests. Each artifact confirmed the others;
none was read by an LLM call. A later refactor (FR-223) moved token
resolution to node then defaults and never consumed the parsed value. Four of
five research personas wanted to wire it; the existing `defaults.max_tokens`
already did the job, so the key was retired and refused at load.

## Trap: gate_checks_shape_not_substance (again)

`assert gc.max_tokens == 2048` passes for a value nothing reads. The witness
was attached to the parser, the one component that cannot tell whether a
setting takes effect.

## Heuristic

A config key's witness test must observe the value at its consumer (here,
the patched executor's `max_tokens` argument), not at its parser. A key with
no consumer-side witness is a claim, not a feature.

**Seed:** How many other `config:`/`defaults:` keys in `graph-v1.json` have
only parser-side tests? A census of schema keys × consumer-side witnesses
would find the next one before an operator does.
