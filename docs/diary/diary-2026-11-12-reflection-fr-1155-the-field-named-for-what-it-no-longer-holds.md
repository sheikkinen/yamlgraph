# Reflection: FR-1155 — the field named for what it no longer holds

**Date:** 2026-11-12
**FR:** FR-1155 (`--token-usage` counts prompt-cache reads and writes)

## What happened

The desk research said "sum `cache_creation`". The live spike said otherwise. On every write, LangChain's
normalised `cache_creation` was 0 and the 2,927 written tokens sat in `ephemeral_5m_input_tokens`. A meter built from
the research alone would have passed its fake-payload tests and then reported zero writes forever. That is a
plausible wrong answer, and nothing would have shown it as wrong.

The same spike changed a ranking. "Warm first, then fan out" was filed as a deferred nicety. Twelve parallel calls
showed that a cold map at width 8 pays eight writes, so at the default width caching *loses* money for maps of about
10 items or fewer. The follow-up note in the FR exists because the measurement contradicted the doc written an hour
earlier.

The judge forced two things:
- AC cases that tell `max` apart from "pick either field". The original equal-overlap case could not.
- The rule that an owed witness never closes FR-1055's gap.

The judge route itself failed twice before it ran. The pinned model was unavailable, and the `claude` backend could
not spawn an npm `.cmd` shim on Windows. Those are platform boundaries, and they were recorded rather than patched.

## Root cause

A normalised field's name is a promise the normaliser does not have to keep. `cache_creation` is still in the
payload; it is simply no longer where the writes are.

## Heuristic

**Fake payloads for a meter must be copied from a live payload, not written from the field names.** Read one raw
record before writing the fixture. The fixture is the claim; the raw record is the evidence.

Second: **a spike that measures the sequential case says nothing about the parallel one.** Concurrency changes cache
economics. Measure the fan-out shape the product actually uses.

## Corrective actions

- Cache read and write counters with `max(cache_creation, ephemeral_5m + ephemeral_1h)`.
- The suffixes `, R cache read` and `, W cache write`.
- A live witness through `system_segments`.
- The map warm-first follow-up recorded in FR-1155.

**Seed:** Should a map node whose sub-prompt carries a cached segment warm on its first item automatically? Would the
new meters, run against game-engine's library map, be the evidence that decides it?
