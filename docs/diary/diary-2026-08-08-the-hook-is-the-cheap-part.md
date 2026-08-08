# Diary 2026-08-08 — The Hook Is the Cheap Part

**Context:** FR-781 enforcement — rebuilding a shell-era DeviantArt
publishing watcher as a governed yamlgraph demo, installed via launchd
`WatchPaths`.

## The trap I walked toward and the adapter walked me back from

I drafted the authoring brief expecting a `type: python` map sub-node,
because the python-map precedent was the nearest pattern in memory. The
adapter's smoke run corrected two assumptions in one pass: `tool_call`
nodes wrap their output under a `result` key (so the map binding is
`over: "{state.unpaired.result}"`, not `{state.unpaired}`), and python
sub-nodes receive whole state dicts, making a `tool_call` sub-node with
explicit `args` the honest shape. Both are *boundary facts about the
runtime*, not opinions — exactly the class of knowledge the governed
authoring route exists to inject. Manual authoring would have shipped
the graph with my wrong priors and debugged them in production logs.
`framework_costume` has a converse: the framework knows its own costume
better than I do.

## The gate that almost passed on shape

`demo_log_semantics.sh` rejected my first witness log: real publish,
real no-op, but no success marker string. My reflex was annoyance —
the log was *substantively* true. But the gate is
`substance_over_presence` running in the other direction: presence of a
machine-checkable marker is what lets the demo-gate stay mechanical.
The cure was one honest summary line, not a gate exemption.

## What the ancestor taught by dying

The shell version kept a `.processed_files` ledger and still
double-published, because rename events re-triggered processing. The
yamlgraph version has no ledger at all: the `.md` twin IS the ledger,
and idempotence falls out of the pairing predicate. Deleting state was
the fix — `growth_as_default` inverted. The confidence gate is the same
move at the semantic layer: rather than post-hoc filtering bad posts,
refuse to publish anything the model won't stake `high` on.

**Heuristic:** When wrapping an LLM behind a file-system trigger, make
the trigger's own artifact (the output file) the idempotence ledger —
any separate ledger will eventually disagree with the filesystem.

**Seed:** The install-hook.sh `--render-only` pattern makes launchd
plists CI-testable without macOS. Could the same dry-run discipline
generalize — every side-effecting installer in `examples/` required to
expose a render/plan mode the test suite can assert on, the way
Terraform separates plan from apply?
