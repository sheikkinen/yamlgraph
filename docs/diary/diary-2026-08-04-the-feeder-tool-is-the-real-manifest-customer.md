# The Feeder Tool Is the Real Manifest Customer

**Date:** 2026-08-04
**Context:** Operator named the key manifest use case: a shared PDF tool —
split by page / chapter / paragraph, chunks fed to a map node, reductions
assembled (summarize each page of a book, then summarize the summaries).
Reflection on what that use case reveals about the FR-768 primitive.

## What the precedent already says

The pattern is not hypothetical — `examples/book_translator` IS it: an LLM
identifies chapter markers, a Python tool splits reliably, a map node fans
the chunks out in parallel, `join_chunks` reduces. It has run for months.
And every one of its four tools (`split_by_markers`, `merge_terms`,
`check_scores`, `join_chunks`) is declared inline and bound to
`examples.book_translator.nodes.*` — locked in the project that grew them.
A book-summarizer wanting the same splitter today would copy the module and
re-declare the block: the exact "re-wrapped per project" duplication FR-768
measured (replicate_tool ×4 families) as its reason to exist. The PDF tool
is the *second strike* on the splitter family, and `second_brief_becomes_graph`
has a sibling: the second consumer of a project-local tool is the moment it
becomes a manifest in `examples/shared/`.

## What the use case exposes about the primitive

The shipped demo (shared-vision-tool) is a **terminal** tool: one
`tool_call`, result to state, END. The PDF splitter is a **feeder** tool: its
output is not a result but an *interface* — a chunk list whose shape a
downstream `over: "{state.chunks.chunks}"` path couples to, stringly-typed.
Three contract surfaces the current manifest does not declare:

1. **Inputs.** `split_pdf(path, mode=page|chapter|paragraph)` — a consumer
   graph cannot discover the args or the mode enum without reading the
   implementation. For a byte-identical duplicated block that was fine (the
   copy WAS the documentation); for a shared declaration it is tribal
   knowledge.
2. **Output shape.** The map node's `over:` path is the coupling point. A
   manifest that names its runtime but not its output contract moves drift
   from YAML blocks (what FR-768 cured) into the tool↔map seam (uncured).
3. **Dependencies.** A PDF splitter needs `pypdf`. Manifests resolve and
   validate at graph load — FR-768's proudest property — but a missing
   third-party dep surfaces at *invocation*, violating the fail-at-load
   principle exactly where a shared tool crosses project boundaries.

None of this argues for building schema machinery now — `growth_as_default`
is the standing trap, and one named consumer is one, not two. But the PDF
tool is precisely the consumer that converts these from speculation into
measurable gaps: it has an arg enum, a contracted output shape, and an
optional dependency. Enforcing it FIRST and watching which of the three
gaps actually bites is cheaper than pre-armoring the manifest model.

## Heuristic

Classify a shared tool as *terminal* or *feeder* before manifesting it. A
terminal tool's manifest needs only the runtime binding; a feeder tool's
real interface is its output shape, and reuse claims for it are unproven
until a map node in a second graph consumes that shape unchanged. The
book-summary pipeline is the acceptance test the manifest primitive has not
yet passed.

**Seed:** The map node knows at graph-load time which state path it iterates;
the manifest knows (or could know) what the tool emits. Could `graph lint`
close the tool↔map seam mechanically — flag an `over:` path that no upstream
tool or schema declares — without adding any runtime machinery at all?
