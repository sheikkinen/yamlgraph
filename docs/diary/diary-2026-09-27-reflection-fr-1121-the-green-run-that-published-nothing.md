# Reflection: FR-1121 — the green run that published nothing

**Date:** 2026-09-27
**FR:** FR-1121 (daily digest ranker under constrained decoding)

## What happened

Nine unattended runs of the digest completed with status success and
published nothing. Every component was correct on its own terms: FR-998
had made the Anthropic binder strict, exactly as judged; FR-905's
formatting boundary correctly treated an absent ranker result as "the
ranker was never invoked"; the runner correctly printed a no-op for
`no_articles`; the workflow correctly committed the database. The
defect lived in none of them. It lived in the policy connecting them:
an `llm` node with no `on_error` falls through to a handler that
records the error and continues, and nothing downstream can tell a
failed predecessor from an empty one.

Two things surprised me. First, `git log --since` beat any
reproduction: the last good run and the first bad run differed by one
minor version, and the diff of that version pointed straight at the
binder. Second, my own RED test was rejected by the judge for the
same reason the incident happened. I had written "assert the graph
declares `on_error: fail`", a check of shape; the judge asked for the
behaviour, "the original exception propagates and the formatting node
never runs". When I wrote that test, its RED log reproduced the
incident in miniature: `Node rank_stories failed`, then
`Executing Python node: format_email`. The shape test would have
passed on a key the compiler did not read; FR-1073's map-level
`on_error` was exactly that key, in the same graph.

## Trap

`composition_bug` wearing `plausible_wrong_answer`: each unit's test
passed, and the system's output passed every shape check (a green job,
a valid commit, a quiet-day status), while being semantically wrong.
The reflex was to add a guard at the runner, where the symptom
surfaced. The runner guard is in the fix, but as the belt, not the
braces; the braces are the node's own policy.

## Heuristic

When a RED test can be written as "the config contains the key", write
it instead as "the run does what the key promises", and read the RED
log before GREEN: if the log shows the incident's own sequence, the
test is the right one. A declaration test proves someone typed the
word; a propagation test proves the compiler read it.

**Seed:** The RED log's fingerprint was "a node failed, and the next
node ran". Could the linter know that shape statically: an `llm` node
without `on_error` whose `state_key` is read by a later node, condition
or template, and warn that the reader cannot distinguish failure from
absence? FR-1124 makes the default `fail`; the lint would name the
graphs that still opt into continuation without a guard.
