# Reflection: FR-1161 — the method that answered for the missing key

**Date:** 2026-11-13
**FR:** FR-1161 (`type: cached_map`, warm-first map dispatch)

## What happened

The judge advised against a core node; the operator overruled and ordered enforcement. `cached_map` runs item 0
alone, then fans items 1..N-1 out together. Both waves come from a snapshot taken at dispatch. The live witness
measured the claim directly: with a 2,946-token shared prefix, `cached_map` wrote the cache once (2,946) and read
it three times (8,838), while plain `map` wrote it four times (11,760) and read nothing. The demo repeated the
shape: 8,800 written, 26,400 read over 4 calls.

Two failures came from boundaries, not from the node. First, the authoring agent's demo failed before any LLM call.
`{state.items}` with no `items` key in state did not raise; it resolved to the state dict's `items` *method*, and
the error surfaced downstream as "got builtin_function_or_method". Second, both authoring-proof checks rejected a
correct report because the agent wrote Windows paths (`examples\demos\...`) and the checks compared strings with
`/`. The files existed; only the separator differed.

The Anthropic meters also misled. `cache_creation` stayed at 0 on every call; the write appeared only under
`ephemeral_5m`. Reading the raw usage records, not the summed field, is what found it.

## Heuristic

**A missing key should never resolve to an attribute.** When a lookup falls back from item access to attribute
access, every method name of the container (`items`, `keys`, `values`, `get`) becomes a silent plausible wrong
answer. The guard belongs where the expression is resolved, not where the wrong type finally fails.

Second: **a proof check that compares path strings has to normalise separators where it reads the report.** The
checker was correct on the host it was written on and wrong on the host it ran on (platform boundary).

**Seed:** Should the expression resolver refuse attribute fallback on dict-backed state entirely, so that
`{state.<name>}` either finds the key or raises "no such state key", and is there any graph that relies on the
fallback today?
