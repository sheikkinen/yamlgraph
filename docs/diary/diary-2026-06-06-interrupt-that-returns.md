# Diary — 2026-06-06 — The Interrupt That Returns Instead of Raising

**FR:** FR-468 — Dungeon Master Web UI
**REQs:** REQ-YG-435 (server+session), REQ-YG-436 (theme+controls), REQ-YG-437 (demo+docs)

## What I built

A FastAPI + HTMX skin over the existing two DM graphs (preplan spine + interrupt
turn loop). No new graph logic — the web layer is pure Presentation (Layer 1)
wrapping Logic (YAML) that already existed. Phased TDD: server/session → theme →
demo/docs, RED before GREEN per phase.

## Cognitive traps encountered

### 1. `workspace_is_not_boundary` — the numbers moved under me

Mid-flight, a concurrent renumbering process (itself the subject of FR-469)
shifted the CAP/REQ/FR space: my intended CAP-166 was claimed by the Meta demo,
the conditional-edge example took REQ-YG-434, and the DM example's own CAP
slid 164→167. I had treated the allocation table as a static snapshot I owned.
It was a shared, live boundary. **Cure applied:** re-verified the free numbers
immediately before writing each numbered artifact, landed on CAP-169 +
REQ-YG-435/436/437, and recorded the reassignment in the FR rather than
silently overwriting.

### 2. The interrupt boundary lies about its shape (J/F1)

My first mental model was "LangGraph raises `GraphInterrupt`, catch it." Wrong.
The compiled graph **returns normally** at the `dm_window` interrupt; the only
honest signal of "paused vs done" is `aget_state(config).next` being non-empty.
`is_complete = not state.next`. Designing the session adapter around the
*exception* would have produced a plausible-but-wrong control flow that passes a
happy-path test and corrupts every real turn. Normalizing at the actual state
boundary — not the imagined one — is the whole game.

### 3. The checkpointer in the YAML is a trap for HTTP (J/F3)

`turn-loop.yaml` declares `checkpointer: sqlite :memory:`. Under a CLI that is
fine — one process, one run. Under HTTP, each request would compile a fresh
`:memory:` store and lose the interrupt state between `/preplan` and `/turn`.
The fix is to override the declared checkpointer with a process-stable
module-level singleton. The lesson: **a config value that is correct for one
runtime can be a defect in another**; the boundary that matters is process
lifetime, not the YAML.

## What made it boring (and therefore right)

Patching the single seam `yamlgraph.node_factory.llm_nodes.execute_prompt`
covered preplan, the parallel `map` sub-nodes, *and* the weave node for both
sync and async invocation. One mock point, deterministic nine-test suite, a
key-free demo that exercises all six controls and ends in a completion panel.
When the test seam is this small, the abstraction is probably right.

## Seed

The interrupt loop's "paused vs done" truth lives in `state.next`, discovered
empirically per-graph. **Could a graph declare its own completion predicate**
(a named state key or a `terminal_when:` expression) so adapters stop
reverse-engineering `state.next` semantics from the runtime — turning an
implicit boundary into a contracted one?
