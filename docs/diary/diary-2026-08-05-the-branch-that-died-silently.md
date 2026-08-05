# The Branch That Died Silently — FR-776 Vision Fallback

**Date:** 2026-08-05
**Context:** FR-776 enforcement — opt-in vision branch for scanned PDFs in
the book-summary demo. RED (43 tests) → GREEN A (shared tools) → author.sh
graph rewiring → GREEN B. 97 tests green across FR-773..776.

## The trap that never got to fire

The frozen RED contract said `partition_chunks` returns
`chunks == text_chunks`. Clean, minimal, obviously correct — and it would
have shipped a run-terminating bug invisible to every unit test: a LangGraph
conditional edge that returns zero `Send`s doesn't error, doesn't warn, it
just ends the branch. An all-blank window on the direct route would have
silently ended the whole run mid-book — no guard, no summary, no exception.

What caught it was not a test but a *pre-implementation doubt*: "what does a
map over an empty list actually do?" Fifteen lines of throwaway StateGraph
answered it empirically (`empty: {...no 'done'...}`) before the graph was
even authored. The cheapest witness of the day was the one that ran against
the platform, not against my code. This is
`does_the_platform_already_do_this` inverted: *does the platform already
NOT do what I'm assuming it does?* Assumed semantics of the orchestration
substrate are external input — normalize at that boundary (verify
empirically), don't trust the mental model.

## The edit that landed in the wrong function

`gate_render` and `merge_vision` were written as deliberate structural
twins. When I added envelope normalization "to gate_render", the
replace-string matched merge_vision's copy of the identical loop header
first. The regression test caught it in seconds (wrong message text), but
the lesson is about symmetric code: when two functions are near-clones,
every context-anchored edit is ambiguous by construction. Anchor edits on
the one line that differs (the state key being iterated), never on the
shared skeleton.

## Compression note

The scanned witness improved when the operator redirected it: my synthetic
scanned.pdf (render text-PDF → PNG → re-wrap) proved the mechanics; his
five-word correction ("use tmp/book3.pdf ... pages 7-9") substituted a
*genuinely* scanned 1939 Finnish book — zero extractable text natively, no
synthetic assembly step to doubt. The witness now proves the actual user
story, not a simulation of it. Real fixtures beat manufactured ones when
they're one `pdfseparate` away.

**Seed:** the empty-fan-out dead-end is a platform behavior every future
map-in-loop graph can hit. Should `yamlgraph graph lint` warn when a map's
`over` feeds from a conditionally-empty source inside a loop — or should
the map compiler itself route zero-item fan-outs straight to the map node's
successor?
