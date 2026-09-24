# The extension point was there; the building block was not

**Date:** 2026-09-24
**Arc:** [issues-2026-09-24.md](../issues-2026-09-24.md) §5 inventory → §6 root
cause

## What happened

The operator asked for an inventory of error handling and intermediate-result
saving, suspecting the latter had been added several times. It had: ten
mechanisms. Three are in the framework: the checkpointer, `skip_if_exists`
(a different problem) and node `cache:`, inert since FR-032 was marked
Implemented. Four were built inside individual graphs; three are proposed,
rejected or superseded. The four-FR map-hardening backlog (FR-955/939/956/957)
is judged and not started, and FR-957's disposal design rests on an
`error_handler` that a 2-branch probe showed never fires for concurrent
branches.

The operator then asked whether the map is too complex as YAML, or missing
extension points. Neither. The map's YAML is four keys, and tool nodes before
and after a map already are the extension point. Every graph-local
reinvention used exactly that point. What none of them could reuse was the
concept each had to invent first: a stable item key. The file name, the
Wikidata QID, the census row ID. The map knows items only by position.

## The trap

`growth_as_default` in its architectural form: when the same workaround
appears four times, the reflex is to add an extension point so the fifth one
looks tidier. An extension point that already exists and is already used by
every workaround is proof the missing thing is a shared *concept*, not a
place to put code. Hooks would have produced a fifth reinvention with
better syntax.

Second trap, in the inventory itself: FR-032 was "Implemented" and FR-957 was
"APPROVED WITH REVISIONS". Both statuses were read-from-source claims. One
compile call without a cache backend, one probe with two branches, and both
claims fell. A status field is a recorded verdict; nothing reads it against
the runtime.

## Heuristic

When the same workaround recurs, list what each copy had to invent before it
could start. The shared prerequisite is the missing primitive; the place the
copies live is usually already the extension point. And a framework feature
marked done is a claim until one run with the smallest non-trivial input
(two branches, two invocations) has exercised it.

**Seed:** What else in YAMLGraph is identified by position or by name where it
should be identified by content? Candidates: prompts (by path, not content
hash, so no cache key and no trace comparison survives a prompt edit),
`state.errors` entries (a list, not keyed by node and item), and FR numbers
(assigned by increment, hence `collision_by_increment`). Which of these, given
a content identity, removes a class of reinvention the way a map `key:`
would?
