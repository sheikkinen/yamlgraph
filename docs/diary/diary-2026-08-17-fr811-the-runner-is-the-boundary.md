# FR-811: The Runner Is the Boundary

The first draft said "programmatic invocation" as though compilation created a
single execution path. It does not. `load_and_compile_async` returns a native
LangGraph object whose `ainvoke` method can bypass every YAMLGraph runner. The
named consumer happened to use `run_graph_async`, but the prose named direct
`ainvoke`; that one-word mismatch made the ideal broader than the mechanism.

The useful correction was not a more ambitious wrapper. It was to name the
supported event precisely: one call to `run_graph_async` is one observable
invocation. That boundary can own graph metadata, exporter initialization,
outcome, resume hashing, and shared route/trace identity without pretending to
control foreign calls on the compiled object. Direct invocation and streaming
remain honest exclusions.

The judge also exposed a planning rule: a required span attribute must have a
failure contract at the proposed seam. Graph name was available during load but
not guaranteed at run time. Attaching validated metadata before caching and
failing before invocation is stronger than inventing `unknown` after context
has already been lost.

**Heuristic:** When an API returns an object with its own execution methods,
"programmatic use" is not a boundary. Name the exact framework-owned runner,
then specify what happens when callers bypass it.

**Seed:** Could compiled graph metadata become a typed, public execution
descriptor so future runners do not depend on private attributes?

## Enforcement Addendum

The focused implementation passed, but the broad suite fired a structural
witness: `executor_async.py` had crossed the repository's 400-line target.
Moving the invocation lifecycle into the existing `observability/otel.py`
boundary made ownership clearer while preserving the public import. It also
avoided increasing the root-module and generated-map inventories. The gates
converted a local feature into a better ownership boundary before the added
behavior could harden in place.

**Heuristic:** A size gate that fires after a coherent feature is evidence that
the feature has named a new responsibility; extract that responsibility rather
than abbreviating it.

**Seed:** Should every public runner have a lifecycle module separate from its
loading and compilation API?
