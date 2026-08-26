# Diary — The Reference That Was Already Committed

**Date:** 2026-08-26
**Context:** Philosopher map-reduce rework with mercury-2 exists only as
uncommitted WIP on a concurrent device. This session needed the pattern
now. No ref here carries it — `git log --all --grep=mercury` and the
remote branch list both came up empty for philosopher work.

## What happened

Instead of waiting for the other device to push (or worse, reconstructing
the WIP from memory of a conversation), a one-minute precedent search
found the pattern already committed:
`examples/demos/prompt_theme_analyzer/graph.yaml` (FR-402) — mercury-2
defaults, `type: map` fan-out with per-item `on_error: skip` and a
`sorted_add` collector, deterministic Python reduce, single grouping LLM
node at the end. The exact map+reduce-on-cheap-model shape the
philosopher rework wants.

## The trap

**WIP-as-reference:** treating uncommitted work on another device as the
canonical design. Cross-device, the only channels that exist are
git-committed files — memory-tool notes, session context, and another
machine's working tree are all machine-local (second confirmation of the
`memory-tool-locality` finding; first was diary 2026-07-16 "a map for the
amnesiac"). An unpushed commit is, from here, indistinguishable from a
commit that was never made.

## The heuristic

When referenced work is unreachable, do not reconstruct it — run the
precedent search the graph-authoring doctrine already mandates. The repo
is older than any one device's WIP; the pattern usually landed once
before. `honor existing patterns` is also the cure for cross-device
amnesia, not just for invention.

Corollary for the concurrent device: push small and early. A pattern
worth referencing from another machine is worth a commit — the push is
the publication act; everything before it is private.

## Seed

Should `now.py` (session introspection) also surface *other-device*
divergence — e.g. a reflog/ref timestamp check per clone pushed to a
shared branch — so "the commit you remember isn't here" becomes a
mechanical situation-check line instead of a discovered surprise?
