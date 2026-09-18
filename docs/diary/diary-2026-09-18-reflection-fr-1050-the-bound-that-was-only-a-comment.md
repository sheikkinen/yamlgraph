# The bound that was only a comment

*2026-09-18 — FR-1050, `loop_limits` binds or fails compilation*

`loop_limits` looked like a safety feature. It read like one in every graph that
declared it, it linted like one (W012 warns when a cycle node has no entry), and
it was documented as one. On ten of the fifteen node types it was a comment with
a colon in it. The value was parsed, stored on the config, carried through
compilation, and never read. Nine graphs across two repos carried 55 such
entries. Every one of them was an author writing down a bound they believed was
in force.

## The trap

`gate_checks_shape_not_substance`, but inverted and turned on the *user*: here
the gate (W012) checked for the *presence* of a `loop_limits` entry and was
satisfied by one that could never fire. The linter's own warning was the thing
teaching authors to add inert entries. A guard that accepts a null guard doesn't
just fail to protect — it manufactures false confidence at scale, because the
warning is the prompt that produces the lie.

The second face of it is `detection_without_enforcement` seen from the config
side. We already know a lint without a blocking gate is advisory. The dual is
less obvious: a *configuration key* without a consuming code path is advisory
too, and it's worse, because a lint at least announces itself as advice while a
YAML key announces itself as a setting.

## The cure that generalises

The fix is not "make the other ten types enforce it" — several genuinely cannot,
and the judgement (R-2) refused that widening. The fix is to make the declaration
*fail* where it cannot bind. Two explicit frozen sets, a union asserted equal to
`NodeType` by a test, and a `GraphConfigError` at load time. The classification
cannot silently drift when a sixteenth node type lands, because the test that
asserts the union goes red the moment someone adds one.

That last part is the transferable move. When you split a domain into
"supported" and "unsupported", the dangerous state is neither set — it's the
member that belongs to *neither*, added later by someone who never read your
module. Assert the partition, not the membership.

## Method note

The migration went through `scripts/author.sh`, and the authoring report — not
the exit code — was the witness. It reported one thing I would have gotten wrong
by hand: the multi-turn demo cannot be driven by `yamlgraph graph run` at all
(checkpointed, needs a thread config and a `Command(resume=...)`), so the smoke
had to be a Python driver. An exit code would have told me "0" either way.

**Seed:** `loop_limits` was found inert because a live investigation (csap
NC-522) tripped over it. How many other YAML keys in this schema are parsed,
validated, stored — and never read by any node type? A mechanical sweep is
cheap: for each field on the graph schema, grep the compile and node-factory
layers for a read. A field with a writer and no reader is a documented promise
with no mechanism behind it. Is that census one graph run away?
