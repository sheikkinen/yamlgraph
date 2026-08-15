# Diary — 2026-08-15 — FR-810: the wrapper was lying about its type

**Context:** Enforcing FR-810 (`parsed_key` router-visible tool_call
outputs), first of the judged trio 810 → 806 → 809.

## What happened

The RED suite (25 witnesses) was written before any implementation and
confirmed failing 22/25. GREEN was mechanical for five of six files —
schema field, factory parameter, compiler wiring, state surface, lint
check — exactly as the judgement froze them. Then the compiled-graph
witness failed with "output is not valid JSON" and exposed a defect the
FR never named: `make_graph_tool_fn` returns
`str(result.get(output_key, result))`. A child graph emitting a dict
produces `{'is_spa': True}` — Python repr, single quotes, `True` — a
string that *looks* like JSON in a log and parses as nothing. Every
graph tool in the codebase has been emitting this type lie since FR-658;
nobody noticed because the only consumer was an LLM, and LLMs read
Python repr as happily as JSON.

## The trap

`plausible_wrong_answer`, wearing a provider costume: the wrapper's
`result` field passed every shape check (it's a string, strings are
fine) while being semantically unparseable. The One Law names the cure
precisely — normalize at the boundary where external data enters. The
graph-tool boundary was coercing with `str()` when it should have been
serializing with `json.dumps`. One conditional at that boundary fixed
the witness; no downstream guard, no tolerant parser in the node
factory.

Second, smaller trap: C901 fired on the factory after the feature
landed — closures accumulate complexity invisibly because each nested
`def` reads as "one statement" while contributing its full branch count.
Extracting `_parse_output`/`_envelope`/`_resolve_tool_args` to module
level was pure motion, zero behavior change, and the diff got *easier*
to review.

## Heuristic

A first *deterministic* consumer is a boundary X-ray. The graph-tool
str() lie survived every LLM consumer because LLMs tolerate any
serialization; the first consumer that had to `json.loads` the output
found the defect in one test run. This is `streaming_xray` generalized:
any tolerant-reader pipeline hides type lies until a strict reader
arrives — so when adding a strict reader, expect to fix the writer.

**Seed:** Which other tool outputs are consumed only by LLMs today?
`shell` and `python` tool results flow through the same wrapper — when
FR-809's orchestrator (or any future deterministic router) starts
reading them, will their serialization survive a strict parse? A
one-shot audit of `str()` coercions at tool boundaries might pre-empt
the next FR-810.
